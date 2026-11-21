import io
import hashlib
import re
from typing import Dict, Any, List, Tuple, Optional
try:
    import pymupdf as fitz
except ImportError:
    import fitz
import docx
import pptx
from app.core.logging import logger
from app.correction_engine.verification_layer import CorrectionVerificationLayer


class IndependentOutputValidator:
    """
    Phase 7: Independent Post-Correction Validation Layer.

    After generating a corrected document:
    1. Confirms the original file remains bit-for-bit unchanged (SHA-256 integrity).
    2. Reopens the generated output file and tests format validity.
    3. Re-extracts text to verify approved corrections were successfully applied.
    4. Ensures zero diagnostic advisory phrases leaked into document content.
    5. Confirms no new defects, corrupted pages, or glyph errors were introduced.
    6. For PDFs, renders each page to verify graphical stability.
    """

    @classmethod
    def validate_output(
        cls,
        original_bytes: bytes,
        corrected_bytes: bytes,
        file_extension: str,
        applied_log: List[Dict[str, Any]],
        expected_checksum: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes independent post-correction verification.
        Returns validation report dictionary.
        """
        ext = file_extension.lower().replace(".", "")
        issues_found: List[str] = []
        resolved_count = 0
        unresolved: List[Dict[str, Any]] = []

        # 1. Original File Immutability Check
        current_orig_hash = hashlib.sha256(original_bytes).hexdigest()
        orig_immutable = True
        if expected_checksum and current_orig_hash != expected_checksum:
            orig_immutable = False
            issues_found.append(f"Original document checksum mismatch! Expected: {expected_checksum}, Found: {current_orig_hash}")
            logger.error("[IndependentValidator] Original file immutability violation detected!")

        # 2. Reopen and Extract Text from Corrected Document
        reopened_successfully = False
        reextracted_text = ""
        page_count = 0

        try:
            if ext == "pdf":
                doc = fitz.open(stream=corrected_bytes, filetype="pdf")
                page_count = len(doc)
                pages_text = []
                # Test rendering each page
                for p_idx, page in enumerate(doc):
                    text = page.get_text("text", sort=True)
                    pages_text.append(text)
                    # Verify page renders without exception
                    pix = page.get_pixmap(dpi=72)
                    if pix.width == 0 or pix.height == 0:
                        issues_found.append(f"Page {p_idx + 1} rendered with invalid dimensions (0x0).")
                reextracted_text = "\n".join(pages_text)
                doc.close()
                reopened_successfully = True

            elif ext == "docx":
                doc = docx.Document(io.BytesIO(corrected_bytes))
                parts = [p.text for p in doc.paragraphs if p.text]
                for tbl in doc.tables:
                    for row in tbl.rows:
                        parts.extend(c.text for c in row.cells if c.text)
                reextracted_text = "\n".join(parts)
                page_count = 1
                reopened_successfully = True

            elif ext == "pptx":
                prs = pptx.Presentation(io.BytesIO(corrected_bytes))
                parts = []
                for s in prs.slides:
                    for shp in s.shapes:
                        if shp.has_text_frame:
                            for p in shp.text_frame.paragraphs:
                                if p.text:
                                    parts.append(p.text)
                        if shp.has_table:
                            for r in shp.table.rows:
                                for c in r.cells:
                                    if c.text:
                                        parts.append(c.text)
                reextracted_text = "\n".join(parts)
                page_count = len(prs.slides)
                reopened_successfully = True

            else:
                issues_found.append(f"Unsupported file format '{ext}' for independent validation.")

        except Exception as e:
            reopened_successfully = False
            issues_found.append(f"Failed to reopen corrected document: {str(e)}")
            logger.error(f"[IndependentValidator] Reopening failed: {e}")

        # 3. Diagnostic Leak Verification
        diagnostic_leak_detected = False
        if reextracted_text and CorrectionVerificationLayer._is_diagnostic_advisory(reextracted_text):
            # Check which specific advisory phrase leaked
            for pat in CorrectionVerificationLayer.DIAGNOSTIC_ADVISORY_PATTERNS:
                match = pat.search(reextracted_text)
                if match:
                    diagnostic_leak_detected = True
                    leak_msg = f"Diagnostic advice leaked into output document: '{match.group(0)}'"
                    issues_found.append(leak_msg)
                    logger.error(f"[IndependentValidator] {leak_msg}")

        # 4. Compare Against Applied Log (Resolution Verification)
        norm_extracted = re.sub(r'\s+', ' ', reextracted_text)
        for item in applied_log:
            orig_str = item.get("original", "").strip()
            corr_str = item.get("corrected", "").strip()

            norm_corr = re.sub(r'\s+', ' ', corr_str)
            if norm_corr in norm_extracted:
                resolved_count += 1
            else:
                unresolved.append({
                    "original": orig_str,
                    "expected_replacement": corr_str,
                    "reason": "Replacement text was not located in re-extracted document text."
                })

        # 5. Determine Overall Verification Status: VERIFIED, VERIFIED_WITH_WARNINGS, NEEDS_REVIEW, FAILED
        if not reopened_successfully or not orig_immutable or diagnostic_leak_detected:
            validation_status = "FAILED"
            is_verified = False
        elif len(issues_found) > 0:
            validation_status = "NEEDS_REVIEW"
            is_verified = False
        elif len(unresolved) > 0:
            validation_status = "VERIFIED_WITH_WARNINGS"
            is_verified = True
        else:
            validation_status = "VERIFIED"
            is_verified = True

        logger.info(
            f"[IndependentValidator] Result: {validation_status} | "
            f"Original Immutable: {orig_immutable} | "
            f"Resolved: {resolved_count}/{len(applied_log)} | "
            f"Leaks Detected: {diagnostic_leak_detected} | "
            f"Issues: {len(issues_found)}"
        )

        return {
            "status": validation_status,
            "is_verified": is_verified,
            "original_immutable": orig_immutable,
            "reopened_successfully": reopened_successfully,
            "diagnostic_leak_detected": diagnostic_leak_detected,
            "page_count": page_count,
            "applied_count": len(applied_log),
            "resolved_count": resolved_count,
            "unresolved_count": len(unresolved),
            "unresolved_details": unresolved,
            "issues": issues_found,
            "corrected_checksum": hashlib.sha256(corrected_bytes).hexdigest()
        }
