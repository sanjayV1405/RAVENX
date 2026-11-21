import io
import re
from typing import Dict, Any, List, Tuple, Optional
import docx
from app.core.logging import logger
from app.correction_engine.verification_layer import CorrectionVerificationLayer


class DOCXCorrector:
    """
    Layout and Style-Preserving DOCX Document Correction Engine.
    
    Applies user-accepted correction findings to Word documents:
    - Traverses body paragraphs, table cells, headers, and footers.
    - Preserves run-level styles (bold, italic, fonts, sizes, colors) where target falls within a run.
    - Retains full document layout, margins, bullet numbering, and image placements.
    - Returns a valid, fully editable .docx file.
    """

    @classmethod
    def correct(
        cls,
        file_bytes: bytes,
        findings: List[Dict[str, Any]]
    ) -> Tuple[bytes, int, List[Dict[str, Any]]]:
        """
        Applies verified findings to the DOCX.
        Returns:
            (corrected_bytes, count_applied, applied_log)
        """
        doc = docx.Document(io.BytesIO(file_bytes))
        
        # Run pre-correction verification
        verified_findings, _ = CorrectionVerificationLayer.verify_findings(findings)

        applied_count = 0
        applied_log: List[Dict[str, Any]] = []

        for finding in verified_findings:
            target_str = finding.get("original_content", "").strip()
            replacement_str = finding.get("suggested_correction", "").strip()
            if not target_str or target_str == replacement_str:
                continue

            replaced_in_doc = False

            # 1. Search & replace in body paragraphs
            for p in doc.paragraphs:
                if target_str in p.text:
                    if cls._replace_in_paragraph(p, target_str, replacement_str):
                        replaced_in_doc = True

            # 2. Search & replace in tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for p in cell.paragraphs:
                            if target_str in p.text:
                                if cls._replace_in_paragraph(p, target_str, replacement_str):
                                    replaced_in_doc = True

            # 3. Search & replace in headers and footers
            for section in doc.sections:
                for p in section.header.paragraphs:
                    if target_str in p.text:
                        if cls._replace_in_paragraph(p, target_str, replacement_str):
                            replaced_in_doc = True
                for p in section.footer.paragraphs:
                    if target_str in p.text:
                        if cls._replace_in_paragraph(p, target_str, replacement_str):
                            replaced_in_doc = True

            if replaced_in_doc:
                applied_count += 1
                applied_log.append({
                    "finding_id": finding.get("id"),
                    "title": finding.get("title"),
                    "original": target_str,
                    "corrected": replacement_str,
                    "status": "applied"
                })

        output_stream = io.BytesIO()
        doc.save(output_stream)
        return output_stream.getvalue(), applied_count, applied_log

    @classmethod
    def _replace_in_paragraph(cls, paragraph, target: str, replacement: str) -> bool:
        """
        Surgically replaces target in paragraph while preserving run-level styling.
        If target spans across multiple runs, character offsets are calculated
        so that unaffected runs and unaffected portions of overlapping runs
        retain their exact bold, italic, font, color, and size attributes.
        """
        if not paragraph.runs:
            if target in paragraph.text:
                paragraph.text = paragraph.text.replace(target, replacement, 1)
                return True
            return False

        # Check single-run exact containment first (fast path)
        for run in paragraph.runs:
            if target in run.text:
                run.text = run.text.replace(target, replacement, 1)
                return True

        # Multi-run character-accurate surgical replacement
        full_text = paragraph.text
        match_idx = full_text.find(target)
        if match_idx == -1:
            return False

        target_len = len(target)
        match_end = match_idx + target_len

        # Build run boundary spans: [(run, start_char, end_char)]
        run_spans = []
        curr_offset = 0
        for run in paragraph.runs:
            run_len = len(run.text)
            run_spans.append((run, curr_offset, curr_offset + run_len))
            curr_offset += run_len

        # Find all runs that overlap with [match_idx, match_end]
        overlapping_indices = []
        for i, (run, r_start, r_end) in enumerate(run_spans):
            # Check for interval overlap
            if max(match_idx, r_start) < min(match_end, r_end):
                overlapping_indices.append(i)

        if not overlapping_indices:
            return False

        # Apply replacement:
        # First overlapping run gets prefix before match_idx + replacement + suffix after match_end (if single run)
        first_idx = overlapping_indices[0]
        last_idx = overlapping_indices[-1]

        first_run, f_start, f_end = run_spans[first_idx]
        prefix = first_run.text[:max(0, match_idx - f_start)]

        if first_idx == last_idx:
            suffix = first_run.text[max(0, match_end - f_start):]
            first_run.text = prefix + replacement + suffix
        else:
            last_run, l_start, l_end = run_spans[last_idx]
            suffix = last_run.text[max(0, match_end - l_start):]

            # Place the replacement in the first overlapping run
            first_run.text = prefix + replacement
            # Clear intermediate runs that were completely inside the target
            for mid_idx in overlapping_indices[1:-1]:
                run_spans[mid_idx][0].text = ""
            # Set suffix in the last overlapping run
            last_run.text = suffix

        return True
