import re
from typing import Dict, Any, List, Optional


class DocumentStructureInspector:
    """
    Module E: Document Structure Intelligence Engine
    Detects structural and organizational anomalies:
    - Heading hierarchy skipping (e.g. H1 immediately followed by H3, skipping H2).
    - Broken numbered section sequences (e.g. Section 1, Section 2, Section 4).
    - Empty or unpopulated tables.
    - Unexpected blank pages situated within active content.
    """

    @classmethod
    def inspect(cls, extraction_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        findings: List[Dict[str, Any]] = []
        pages = extraction_data.get("pages", [])

        if not pages:
            return findings

        # Cross-page state variables (must persist across the loop)
        last_heading_level = 0
        last_heading_title = ""
        numbered_section_pattern = re.compile(r'^(?:Section\s+)?([1-9][0-9]?)\.\s+([A-Za-z].*)$', re.MULTILINE)
        last_section_num = 0
        seen_sections: set = set()

        for page in pages:
            page_num = page.get("page_number", 1)
            raw_text = page.get("reconstructed_text") or page.get("raw_text", "")

            # 1. Heading Hierarchy Gaps from explicit heading objects
            structured = page.get("structured_data", {})
            headings = structured.get("headings", []) or page.get("headings", [])
            for h in headings:
                level = h.get("level", 1) if isinstance(h, dict) else 1
                title = h.get("text", "") if isinstance(h, dict) else str(h)
                if last_heading_level > 0 and level > (last_heading_level + 1):
                    findings.append({
                        "category": "structural",
                        "title": f"Skipped heading level hierarchy (H{last_heading_level} to H{level})",
                        "finding_classification": "A",
                        "is_actionable": False,
                        "page_number": page_num,
                        "original_content": f"'{last_heading_title}' (H{last_heading_level}) followed by '{title}' (H{level})",
                        "suggested_correction": f"Demote to H{last_heading_level + 1} or insert intervening H{last_heading_level + 1} section",
                        "explanation": f"Document heading hierarchy jumps directly from level {last_heading_level} to {level}, skipping level {last_heading_level + 1}.",
                        "severity": "medium",
                        "confidence": 0.94,
                        "evidence_source": "document_structure_engine",
                        "detection_method": "rule_based"
                    })
                last_heading_level = level
                last_heading_title = title

            # 2. Numbered Section Sequence across all pages
            for match in numbered_section_pattern.finditer(raw_text):
                sec_num = int(match.group(1))
                sec_title = match.group(2).strip()

                if sec_num in seen_sections:
                    findings.append({
                        "category": "structural",
                        "title": f"Duplicate section number '{sec_num}'",
                        "finding_classification": "A",
                        "is_actionable": False,
                        "page_number": page_num,
                        "original_content": match.group(0),
                        "suggested_correction": "Renumber section sequentially",
                        "explanation": f"Section number {sec_num} ('{sec_title}') was already used earlier in the document.",
                        "severity": "high",
                        "confidence": 0.95,
                        "evidence_source": "document_structure_engine",
                        "detection_method": "rule_based"
                    })
                elif last_section_num > 0 and sec_num > last_section_num + 1:
                    missing = last_section_num + 1
                    findings.append({
                        "category": "structural",
                        "title": f"Broken numbering sequence: jumped from {last_section_num} to {sec_num}",
                        "finding_classification": "A",
                        "is_actionable": False,
                        "page_number": page_num,
                        "original_content": match.group(0),
                        "suggested_correction": f"Check for missing Section {missing} or renumber to {missing}",
                        "explanation": f"Numbered section sequence skipped from {last_section_num} to {sec_num} (Section {missing} is absent).",
                        "severity": "high",
                        "confidence": 0.92,
                        "evidence_source": "document_structure_engine",
                        "detection_method": "rule_based"
                    })

                seen_sections.add(sec_num)
                last_section_num = sec_num

            # Check Empty Tables
            tables = structured.get("tables", []) or page.get("tables", [])
            for table in tables:
                rows = table.get("rows", []) or table.get("data", []) if isinstance(table, dict) else table if isinstance(table, list) else []
                is_empty = False
                if not rows:
                    is_empty = True
                else:
                    total_cells = sum(len(row) for row in rows if isinstance(row, list))
                    non_empty_cells = sum(1 for row in rows if isinstance(row, list) for c in row if str(c).strip())
                    if total_cells > 0 and non_empty_cells == 0:
                        is_empty = True

                if is_empty:
                    findings.append({
                        "category": "structural",
                        "title": "Empty table detected",
                        "finding_classification": "A",
                        "is_actionable": False,
                        "page_number": page_num,
                        "original_content": "[Empty Table with no data cells]",
                        "suggested_correction": "Populate table data or remove table placeholder",
                        "explanation": f"Table on page {page_num} contains no populated cells or data entries.",
                        "severity": "medium",
                        "confidence": 0.97,
                        "evidence_source": "document_structure_engine",
                        "detection_method": "rule_based"
                    })

        # Check unexpected blank pages in multi-page documents (blank page flanked by populated pages)
        num_pages = len(pages)
        if num_pages >= 3:
            for idx in range(1, num_pages - 1):
                cur_page = pages[idx]
                prev_page = pages[idx - 1]
                next_page = pages[idx + 1]

                cur_text = cur_page.get("raw_text", "").strip()
                prev_text = prev_page.get("raw_text", "").strip()
                next_text = next_page.get("raw_text", "").strip()

                if not cur_text and prev_text and next_text:
                    p_num = cur_page.get("page_number", idx + 1)
                    findings.append({
                        "category": "structural",
                        "title": "Unexpected blank page inside document body",
                        "finding_classification": "A",
                        "is_actionable": False,
                        "page_number": p_num,
                        "original_content": f"[Page {p_num} is completely empty]",
                        "suggested_correction": "Remove blank page or verify if intentional section separator",
                        "explanation": f"Page {p_num} contains no text blocks or elements, situated between populated pages {idx} and {idx + 2}.",
                        "severity": "low",
                        "confidence": 0.91,
                        "evidence_source": "document_structure_engine",
                        "detection_method": "rule_based"
                    })

        return findings
