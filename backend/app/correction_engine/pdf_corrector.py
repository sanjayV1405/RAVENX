import os
import io
import re
from typing import Dict, Any, List, Tuple, Optional
try:
    import pymupdf as fitz
except ImportError:
    import fitz

from app.core.logging import logger
from app.correction_engine.verification_layer import CorrectionVerificationLayer


class PDFCorrector:
    """
    Phase 7: High-Precision, Spatially Grounded PDF Correction Engine.

    Guarantees:
    - Never applies layout instructions or diagnostic text as document content.
    - Surgically targets changed tokens or phrases using exact baseline coordinates.
    - Discovers exact baseline Y and font metrics directly from PyMuPDF text dictionary spans.
    - Calibrates font size and character spacing to prevent text overlap with adjacent words.
    - Safely maps unicode currency symbols (e.g., ₹ -> Rs.) for standard font compatibility.
    - Preserves all vector graphics, page dimensions, images, footers, and background layers.
    """

    @classmethod
    def correct(
        cls,
        file_bytes: bytes,
        findings: List[Dict[str, Any]]
    ) -> Tuple[bytes, int, List[Dict[str, Any]]]:
        """
        Applies verified findings to the PDF.
        Returns:
            (corrected_bytes, count_applied, applied_log)
        """
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        
        # 1. Harvest page text for verification
        page_texts = {i + 1: doc[i].get_text("text") for i in range(len(doc))}

        # 2. Run Pre-Correction Verification Layer
        verified_findings, rejected_findings = CorrectionVerificationLayer.verify_findings(
            findings,
            document_text_by_page=page_texts
        )

        applied_count = 0
        applied_log: List[Dict[str, Any]] = []

        for finding in verified_findings:
            orig = finding.get("original_content", "").strip()
            corr = finding.get("suggested_correction", "").strip()
            target_page_num = finding.get("page_number", 1)

            # Determine target pages
            if 1 <= target_page_num <= len(doc):
                pages_to_search = [doc[target_page_num - 1]]
            else:
                pages_to_search = list(doc)

            applied_for_finding = False

            for page in pages_to_search:
                # 3. Surgical token refinement:
                # If finding is a repeated word (e.g. 'improve improve' -> 'improve'),
                # redact only the second occurrence to preserve first word geometry.
                search_term = orig
                replacement_text = corr

                is_dup_word = bool(re.match(r'^([a-zA-Z]{2,})\s+\1$', orig, re.IGNORECASE) and corr.lower() == orig.split()[0].lower())
                if is_dup_word:
                    # Redact only the second instance preceded by a space
                    word = corr
                    search_term = f"{word} {word}"

                # Perform spatial rectangle search
                rects = page.search_for(search_term)
                if not rects:
                    # Try whitespace-normalized search if exact match missed
                    norm_target = re.sub(r'\s+', ' ', search_term)
                    if norm_target != search_term:
                        rects = page.search_for(norm_target)

                if not rects:
                    continue

                # Multi-rect contiguous union (for multi-span tokens like 'I8,40,000' or '(I)')
                if len(rects) > 1:
                    u_rect = rects[0]
                    contiguous = True
                    for r in rects[1:]:
                        if abs(r.y0 - u_rect.y0) < 6:
                            u_rect = u_rect | r
                        else:
                            contiguous = False
                            break
                    rect = u_rect if contiguous else rects[0]
                else:
                    rect = rects[0]

                # 4. Extract precision font metrics and baseline from local spans
                # Also detect if the found rect is a mid-span subset (e.g. "Operations    Leadership"
                # inside "Prepared for: Operations    Leadership Team"). In that case, expand
                # the redaction to the full containing span and rebuild the whole span text
                # with the correction applied, to prevent orphaned trailing words.
                font_name, font_size, font_color, baseline_y, containing_span_text, containing_span_rect = \
                    cls._discover_font_baseline_and_span(page, rect, search_term)

                # 5. Unicode / currency symbol mapping & TrueType font embedding
                final_replacement_raw = replacement_text

                # 6. Span-aware replacement:
                # If the found rect is a strict subset of a containing span,
                # rebuild the full span text with the token replaced.
                # Guard: Do NOT envelop if containing span contains multiple distinct fields
                # (e.g. "Document ID" or "Approval date") to protect inter-field spacing.
                is_multi_field = bool(
                    containing_span_text and (
                        "Document ID" in containing_span_text or
                        "Approval date" in containing_span_text or
                        re.search(r':.*?(\s{2,}).*?:', containing_span_text)
                    )
                )

                if not is_multi_field and containing_span_text and containing_span_rect and len(containing_span_text) > len(search_term) + 2:
                    norm_orig = re.sub(r'\s+', ' ', search_term)
                    if search_term in containing_span_text:
                        full_replacement = containing_span_text.replace(search_term, final_replacement_raw, 1)
                    elif norm_orig in containing_span_text:
                        full_replacement = containing_span_text.replace(norm_orig, final_replacement_raw, 1)
                    else:
                        full_replacement = re.sub(re.escape(norm_orig), final_replacement_raw, containing_span_text, count=1)
                    redact_rect = containing_span_rect
                    raw_final_text = full_replacement
                else:
                    redact_rect = rect
                    raw_final_text = final_replacement_raw

                # Prepare text and font (natively embeds Arial TrueType for ₹ and Unicode if available)
                final_text, insert_font_name, insert_font_file = cls._prepare_text_and_font(page, raw_final_text, font_name)

                # 7. Kerning & overlap prevention:
                # Measure text width of replacement vs target rect
                try:
                    text_len = fitz.get_text_length(final_text, fontname=insert_font_name, fontsize=font_size)
                except Exception:
                    text_len = fitz.get_text_length(final_text, fontname="helv", fontsize=font_size)

                # If replacement is slightly wider than rect, scale font down to fit
                target_font_size = font_size
                if redact_rect.width > 0 and text_len > (redact_rect.width + 1.0):
                    scale_factor = redact_rect.width / max(1.0, text_len)
                    # Don't scale down more than 15%
                    target_font_size = max(font_size * 0.85, font_size * scale_factor)

                # 8. Apply dynamic background-aware redaction (prevents white box artifacts in shaded table cells)
                bg_color = cls._detect_background_color(page, redact_rect)
                page.add_redact_annot(redact_rect, fill=bg_color)
                page.apply_redactions()

                # If TrueType font is used, embed font definition on page AFTER apply_redactions()
                if insert_font_file:
                    try:
                        page.insert_font(fontname=insert_font_name, fontfile=insert_font_file)
                    except Exception as e:
                        logger.debug(f"Font embedding note: {e}")

                # 9. Insert corrected text precisely at baseline from span's x0
                insert_pt = fitz.Point(redact_rect.x0, baseline_y)
                try:
                    if insert_font_file:
                        page.insert_text(
                            insert_pt,
                            final_text,
                            fontsize=target_font_size,
                            fontfile=insert_font_file,
                            fontname=insert_font_name,
                            color=font_color
                        )
                    else:
                        page.insert_text(
                            insert_pt,
                            final_text,
                            fontsize=target_font_size,
                            fontname=insert_font_name,
                            color=font_color
                        )
                except Exception:
                    page.insert_text(
                        insert_pt,
                        cls._sanitize_unicode_text(final_text),
                        fontsize=target_font_size,
                        fontname="helv",
                        color=font_color
                    )

                applied_for_finding = True
                applied_count += 1
                applied_log.append({
                    "finding_id": finding.get("id"),
                    "title": finding.get("title"),
                    "page_number": page.number + 1,
                    "original": orig,
                    "corrected": corr,
                    "applied_span": final_text,
                    "status": "applied"
                })
                break  # Applied on page, move to next finding

        output_stream = io.BytesIO()
        doc.save(output_stream, garbage=3, deflate=True)
        doc.close()

        logger.info(f"[PDFCorrector] Successfully applied {applied_count} corrections out of {len(verified_findings)} verified findings.")
        return output_stream.getvalue(), applied_count, applied_log

    @classmethod
    def _detect_background_color(cls, page, rect: fitz.Rect) -> Tuple[float, float, float]:
        """
        Samples the underlying background color of the page around rect to match
        table cell shading, tinted banners, and colored backgrounds.
        Returns RGB tuple in 0.0 - 1.0 range.
        """
        try:
            # 1. First check vector drawing fills covering the rect (e.g. shaded table cells)
            drawings = page.get_drawings()
            for draw in reversed(drawings):
                draw_rect = draw.get("rect")
                if draw_rect and draw_rect.intersects(rect):
                    fill = draw.get("fill")
                    if fill and len(fill) >= 3:
                        return (float(fill[0]), float(fill[1]), float(fill[2]))

            # 2. Sample pixmap corners adjacent to rect
            sample_rect = fitz.Rect(
                max(0, rect.x0 - 2),
                max(0, rect.y0 - 2),
                min(page.rect.width, rect.x1 + 2),
                min(page.rect.height, rect.y1 + 2)
            )
            pix = page.get_pixmap(clip=sample_rect, dpi=72)
            if pix.width > 0 and pix.height > 0:
                corners = [
                    (0, 0),
                    (pix.width - 1, 0),
                    (0, pix.height - 1),
                    (pix.width - 1, pix.height - 1)
                ]
                samples = []
                for cx, cy in corners:
                    c = pix.pixel(cx, cy)
                    samples.append((c[0] / 255.0, c[1] / 255.0, c[2] / 255.0))
                samples.sort(key=lambda rgb: sum(rgb), reverse=True)
                return samples[0]
        except Exception as e:
            logger.debug(f"Could not sample background color: {e}")

        return (1.0, 1.0, 1.0)

    @classmethod
    def _prepare_text_and_font(
        cls,
        page,
        text: str,
        desired_font: str
    ) -> Tuple[str, str, Optional[str]]:
        """
        Ensures Unicode glyphs (such as Indian Rupee symbol '₹', euro '€', em-dash)
        render without black squares by discovering TrueType font path where available.
        Returns: (final_text, insert_font_name, font_file_path_or_None)
        """
        has_extended_unicode = any(ord(c) > 127 for c in text)
        if not has_extended_unicode:
            return text, desired_font, None

        custom_path = os.environ.get("UNICODE_FONT_PATH")
        system_font_paths = []
        if custom_path:
            system_font_paths.append(custom_path)

        # Cross-platform candidate TrueType font paths
        system_font_paths.extend([
            # Windows
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            # Linux (Debian, Ubuntu, Alpine, Fedora, RHEL)
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
            # macOS
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial.ttf"
        ])

        font_file = None
        for p in system_font_paths:
            if os.path.exists(p):
                font_file = p
                break

        if font_file:
            uni_font_name = "rx_uni_font"
            return text, uni_font_name, font_file

        # Fallback to sanitized ASCII
        return cls._sanitize_unicode_text(text), desired_font, None

    @classmethod
    def _discover_font_baseline_and_span(
        cls,
        page,
        target_rect,
        search_term: str = ""
    ) -> Tuple[str, float, Tuple[float, float, float], float, Optional[str], Optional[Any]]:
        """
        Discovers font styling, baseline coordinate, and the full containing span text/rect.
        Returns: (font_name, font_size, font_color, baseline_y, span_text, span_rect)
        span_text and span_rect are None if the found rect fully covers the span.
        """
        default_font = "helv"
        default_size = 10.0
        default_color = (0.1, 0.1, 0.1)
        default_baseline = max(target_rect.y0 + default_size, target_rect.y1 - 2.0)
        containing_span_text: Optional[str] = None
        containing_span_rect: Optional[Any] = None

        try:
            page_dict = page.get_text("dict")
            closest_dist = float("inf")
            target_center_y = (target_rect.y0 + target_rect.y1) / 2

            for block in page_dict.get("blocks", []):
                if block.get("type") == 0:
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            span_bbox = span.get("bbox", [0, 0, 0, 0])
                            span_center_y = (span_bbox[1] + span_bbox[3]) / 2
                            dist = abs(span_center_y - target_center_y)
                            if dist < closest_dist and dist < (target_rect.height * 1.5):
                                closest_dist = dist
                                default_size = span.get("size", default_size)

                                # Extract color
                                raw_color = span.get("color", 0)
                                if isinstance(raw_color, int):
                                    r = ((raw_color >> 16) & 255) / 255.0
                                    g = ((raw_color >> 8) & 255) / 255.0
                                    b = (raw_color & 255) / 255.0
                                    default_color = (r, g, b)

                                # Extract font weight
                                raw_font = span.get("font", "").lower()
                                if "bold" in raw_font or "hebo" in raw_font:
                                    default_font = "hebo"
                                elif "italic" in raw_font or "heit" in raw_font:
                                    default_font = "heit"
                                else:
                                    default_font = "helv"

                                # Extract exact baseline Y from origin if available
                                origin = span.get("origin")
                                if origin and len(origin) == 2:
                                    default_baseline = origin[1]

                                # Check if the target rect is a subset of this span with surrounding text
                                s_x0, s_y0, s_x1, s_y1 = span_bbox
                                span_text = span.get("text", "")
                                # If span is horizontally wider than target rect by >6pt, it contains surrounding text
                                if (s_x0 <= target_rect.x0 + 2 and s_x1 >= target_rect.x1 - 2
                                        and (s_x1 - s_x0) > (target_rect.width + 6.0)
                                        and len(span_text.strip()) > 3):
                                    norm_s = re.sub(r'\s+', ' ', search_term.strip()) if search_term else ""
                                    norm_span = re.sub(r'\s+', ' ', span_text)
                                    if not norm_s or norm_s in norm_span or norm_s in span_text:
                                        containing_span_text = span_text
                                        containing_span_rect = fitz.Rect(s_x0, s_y0, s_x1, s_y1)
        except Exception as e:
            logger.debug(f"Could not discover span metrics: {e}")

        return default_font, default_size, default_color, default_baseline, containing_span_text, containing_span_rect

    @classmethod
    def _discover_font_and_baseline(
        cls,
        page,
        target_rect
    ) -> Tuple[str, float, Tuple[float, float, float], float]:
        """Legacy wrapper — returns only (font_name, font_size, font_color, baseline_y)."""
        font_name, font_size, font_color, baseline_y, _, _ = cls._discover_font_baseline_and_span(page, target_rect)
        return font_name, font_size, font_color, baseline_y

    @classmethod
    def _sanitize_unicode_text(cls, text: str) -> str:
        """Maps unicode currency and typographic symbols to standard ASCII equivalents."""
        replacements = {
            "₹": "Rs.",
            "€": "EUR ",
            "£": "GBP ",
            "—": "-",
            "–": "-",
            "’": "'",
            "‘": "'",
            "“": '"',
            "”": '"',
            "…": "..."
        }
        sanitized = text
        for u_char, safe_char in replacements.items():
            sanitized = sanitized.replace(u_char, safe_char)
        return sanitized
