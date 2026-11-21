import io
from typing import Dict, Any, List, Tuple
try:
    import pymupdf as fitz
except ImportError:
    import fitz


class PDFExtractor:
    """
    Extracts text, typography, visual coordinates, and bounding geometry from PDF documents using PyMuPDF.

    Key improvements (Phase 5.1):
    - Span/line-aware text joining: adds spaces where PyMuPDF omits them between adjacent spans.
    - Word-level bounding-box extraction for spatial reconstruction.
    - Table region detection: blocks inside table bounding boxes are marked is_table_block=True.
    - reconstructed_text per page built from word-level bboxes preserves correct spacing.
    """

    # Minimum horizontal gap (points) between span end and next span start
    # that indicates a word boundary / space is needed.
    SPAN_SPACE_GAP_THRESHOLD = 1.0

    @classmethod
    def _build_block_text(cls, block: Dict) -> str:
        """Join span texts with space-awareness between spans on the same line,
        and with a single space between lines in the block."""
        line_texts: List[str] = []
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            if not spans:
                continue
            span_parts: List[str] = []
            prev_x1: float = None  # type: ignore
            for span in spans:
                span_text = span.get("text", "")
                span_bbox = span.get("bbox", [0, 0, 0, 0])
                x0 = span_bbox[0]
                x1 = span_bbox[2]
                if prev_x1 is not None:
                    gap = x0 - prev_x1
                    if gap > cls.SPAN_SPACE_GAP_THRESHOLD:
                        # Visible gap between spans — insert space
                        span_parts.append(" ")
                span_parts.append(span_text)
                prev_x1 = x1
            line_text = "".join(span_parts)
            if line_text.strip():
                line_texts.append(line_text)
        # Join lines with space (line breaks in PDF blocks are logical line breaks)
        return " ".join(line_texts).strip()

    @classmethod
    def _get_table_bboxes(cls, page) -> List[Tuple[float, float, float, float]]:
        """Return list of (x0,y0,x1,y1) bboxes for tables found on the page."""
        bboxes: List[Tuple[float, float, float, float]] = []
        try:
            if hasattr(page, "find_tables"):
                tabs = page.find_tables()
                for tab in tabs:
                    bboxes.append(tuple(tab.bbox))  # type: ignore
        except Exception:
            pass
        return bboxes

    @classmethod
    def _bbox_overlaps(cls, block_bbox: List[float], table_bboxes: List[Tuple]) -> bool:
        """Return True if block_bbox centre falls inside any table bbox."""
        bx0, by0, bx1, by1 = block_bbox
        cx = (bx0 + bx1) / 2
        cy = (by0 + by1) / 2
        for (tx0, ty0, tx1, ty1) in table_bboxes:
            if tx0 <= cx <= tx1 and ty0 <= cy <= ty1:
                return True
        return False

    @classmethod
    def _build_reconstructed_text(cls, page) -> str:
        """Build spatially-correct page text from word-level bboxes.
        Words are sorted by (y_bucket, x) and joined with spaces / newlines."""
        try:
            words = page.get_text("words")  # list of (x0,y0,x1,y1,word,block,line,word_idx)
        except Exception:
            return page.get_text() or ""

        if not words:
            return page.get_text() or ""

        # Sort words by approximate reading order: bucket by y (line height ~12pt)
        LINE_HEIGHT = 12.0
        sorted_words = sorted(words, key=lambda w: (round(w[1] / LINE_HEIGHT), w[0]))

        lines: List[List] = []
        current_line: List = []
        last_y_bucket = None

        for w in sorted_words:
            y_bucket = round(w[1] / LINE_HEIGHT)
            if last_y_bucket is None or y_bucket == last_y_bucket:
                current_line.append(w)
            else:
                if current_line:
                    lines.append(current_line)
                current_line = [w]
            last_y_bucket = y_bucket

        if current_line:
            lines.append(current_line)

        line_strings: List[str] = []
        for line_words in lines:
            line_strings.append(" ".join(w[4] for w in sorted(line_words, key=lambda w: w[0])))

        return "\n".join(line_strings)

    @classmethod
    def extract(cls, file_bytes: bytes) -> Dict[str, Any]:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        page_count = len(doc)
        if page_count == 0:
            doc.close()
            raise ValueError("Corrupt or unreadable PDF: document contains 0 pages.")
        pages: List[Dict[str, Any]] = []
        total_raw_text: List[str] = []
        has_any_ocr_needed = False

        meta = {
            "title": doc.metadata.get("title") or "",
            "author": doc.metadata.get("author") or "",
            "subject": doc.metadata.get("subject") or "",
            "creator": doc.metadata.get("creator") or "",
            "producer": doc.metadata.get("producer") or "",
            "format": "PDF",
            "page_count": page_count,
            "is_encrypted": doc.is_encrypted,
        }

        for page_idx in range(page_count):
            page = doc[page_idx]
            page_num = page_idx + 1
            rect = page.rect
            width, height = rect.width, rect.height

            # Raw text (PyMuPDF's natural output — already has correct line breaks)
            raw_text = page.get_text() or ""
            total_raw_text.append(raw_text)
            word_count = len(raw_text.split())

            # Detect if page lacks extractable text layer (scanned page candidate)
            needs_ocr = len(raw_text.strip()) < 15
            if needs_ocr:
                has_any_ocr_needed = True

            # Spatially-reconstructed text using word-level bboxes
            reconstructed_text = cls._build_reconstructed_text(page)

            # Table bboxes (used to mark blocks that come from table regions)
            table_bboxes = cls._get_table_bboxes(page)

            # Extract detailed block geometry & typography
            page_dict = page.get_text("dict")
            blocks_data: List[Dict[str, Any]] = []
            fonts_used = set()
            headings: List[Dict[str, Any]] = []

            for block in page_dict.get("blocks", []):
                # block type 0 is text
                if block.get("type") == 0:
                    bbox = [round(c, 2) for c in block.get("bbox", [0, 0, 0, 0])]
                    is_table_block = cls._bbox_overlaps(bbox, table_bboxes)

                    block_lines: List[Dict[str, Any]] = []

                    for line in block.get("lines", []):
                        line_bbox = [round(c, 2) for c in line.get("bbox", [0, 0, 0, 0])]
                        spans_data = []

                        for span in line.get("spans", []):
                            span_text = span.get("text", "")
                            font_name = span.get("font", "Unknown")
                            font_size = round(span.get("size", 0.0), 2)
                            fonts_used.add(font_name)

                            # Heuristic for headings based on font size (>= 14pt)
                            if font_size >= 14 and len(span_text.strip()) > 0:
                                headings.append({
                                    "text": span_text.strip(),
                                    "font_size": font_size,
                                    "font_name": font_name,
                                    "bbox": [round(c, 2) for c in span.get("bbox", [0, 0, 0, 0])]
                                })

                            spans_data.append({
                                "text": span_text,
                                "font": font_name,
                                "size": font_size,
                                "flags": span.get("flags", 0),
                                "color": span.get("color", 0),
                                "bbox": [round(c, 2) for c in span.get("bbox", [0, 0, 0, 0])]
                            })

                        block_lines.append({
                            "bbox": line_bbox,
                            "spans": spans_data
                        })

                    # Build block text with space-aware joining
                    block_text = cls._build_block_text(block)

                    blocks_data.append({
                        "bbox": bbox,
                        "text": block_text,
                        "is_table_block": is_table_block,
                        "lines": block_lines
                    })

            # Check for tabular structures (find_tables if supported)
            tables_data: List[Dict[str, Any]] = []
            try:
                if hasattr(page, "find_tables"):
                    tabs = page.find_tables()
                    if not tabs.tables:
                        tabs = page.find_tables(vertical_strategy="text")
                    for t_idx, tab in enumerate(tabs):
                        extracted_table = tab.extract()
                        if extracted_table:
                            tables_data.append({
                                "table_index": t_idx + 1,
                                "bbox": [round(c, 2) for c in tab.bbox],
                                "row_count": len(extracted_table),
                                "col_count": len(extracted_table[0]) if extracted_table else 0,
                                "rows": extracted_table
                            })
            except Exception:
                tables_data = []

            has_tables = len(tables_data) > 0

            pages.append({
                "page_number": page_num,
                "width": round(width, 2),
                "height": round(height, 2),
                "raw_text": raw_text,
                "reconstructed_text": reconstructed_text,
                "word_count": word_count,
                "has_tables": has_tables,
                "needs_ocr": needs_ocr,
                "extraction_method": "native",
                "ocr_confidence": None,
                "structured_data": {
                    "dimensions": {"width": round(width, 2), "height": round(height, 2)},
                    "word_count": word_count,
                    "fonts": sorted(list(fonts_used)),
                    "headings": headings,
                    "blocks_count": len(blocks_data),
                    "blocks": blocks_data,
                    "tables": tables_data,
                }
            })

        doc.close()

        meta["has_scanned_pages"] = has_any_ocr_needed

        return {
            "extractor_type": "pdf",
            "page_count": page_count,
            "metadata": meta,
            "raw_text": "\n\n".join(total_raw_text),
            "pages": pages,
        }
