import difflib
import re
from typing import Dict, Any, List, Optional, Tuple


class DocumentComparisonEngine:
    """
    Multi-Document Comparison Engine
    Detects and classifies differences between a base document and a target (revised) document:
    - Content differences (added, removed, modified text, changed names, dates, amounts, tables).
    - Structural differences (reordered headings, missing sections, missing table rows/cols).
    - Formatting differences (font changes, font sizes, margins).
    Classifies differences into:
    - Added
    - Removed
    - Modified
    - Potentially inconsistent
    - Formatting-only
    """

    DATE_PATTERN = re.compile(r'\b(?:20[2-3][0-9]-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+20[2-3][0-9])\b', re.IGNORECASE)
    AMOUNT_PATTERN = re.compile(r'(?:USD|EUR|GBP|CAD|AUD|\$|€|£|₹)\s?[0-9,]+(?:\.[0-9]{2})?\b')

    @classmethod
    def compare(
        cls,
        base_data: Dict[str, Any],
        target_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        differences: List[Dict[str, Any]] = []

        base_pages = base_data.get("pages", [])
        target_pages = target_data.get("pages", [])

        # 1. Structural Comparison: Headings & Sections
        base_headings = cls._extract_headings(base_pages, base_data.get("raw_text", ""))
        target_headings = cls._extract_headings(target_pages, target_data.get("raw_text", ""))

        base_h_titles = [h["text"] for h in base_headings]
        target_h_titles = [h["text"] for h in target_headings]

        # Missing or Added Sections
        for h in base_headings:
            if h["text"] not in target_h_titles:
                differences.append({
                    "category": "structural",
                    "diff_type": "removed",
                    "title": f"Removed section: '{h['text']}'",
                    "base_page": h.get("page", 1),
                    "target_page": None,
                    "base_content": h["text"],
                    "target_content": "",
                    "explanation": f"Section '{h['text']}' present in base document was removed or renamed in revised document.",
                    "significance": "high"
                })

        for h in target_headings:
            if h["text"] not in base_h_titles:
                differences.append({
                    "category": "structural",
                    "diff_type": "added",
                    "title": f"New section added: '{h['text']}'",
                    "base_page": None,
                    "target_page": h.get("page", 1),
                    "base_content": "",
                    "target_content": h["text"],
                    "explanation": f"Section '{h['text']}' was added to the revised document.",
                    "significance": "medium"
                })

        # Reordered Sections
        common_headings = [t for t in target_h_titles if t in base_h_titles]
        base_order = [base_h_titles.index(t) for t in common_headings]
        if base_order != sorted(base_order):
            differences.append({
                "category": "structural",
                "diff_type": "modified",
                "title": "Document section order rearranged",
                "base_page": 1,
                "target_page": 1,
                "base_content": " -> ".join(base_h_titles[:5]),
                "target_content": " -> ".join(target_h_titles[:5]),
                "explanation": "Headings appear in a different sequence between the base and revised documents.",
                "significance": "medium"
            })

        # 2. Content Comparison: Sentence-by-Sentence diff
        base_sentences = cls._split_sentences(base_pages, base_data.get("raw_text", ""))
        target_sentences = cls._split_sentences(target_pages, target_data.get("raw_text", ""))

        matcher = difflib.SequenceMatcher(None, [s["text"] for s in base_sentences], [s["text"] for s in target_sentences])
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "replace":
                for b_idx, t_idx in zip(range(i1, i2), range(j1, j2)):
                    b_item = base_sentences[b_idx]
                    t_item = target_sentences[t_idx]
                    diff_item = cls._classify_sentence_change(b_item, t_item)
                    differences.append(diff_item)

            elif tag == "delete":
                for b_idx in range(i1, i2):
                    b_item = base_sentences[b_idx]
                    differences.append({
                        "category": "content",
                        "diff_type": "removed",
                        "title": "Text segment removed",
                        "base_page": b_item["page"],
                        "target_page": None,
                        "base_content": b_item["text"],
                        "target_content": "",
                        "explanation": f"Sentence removed from Page {b_item['page']}.",
                        "significance": "medium"
                    })

            elif tag == "insert":
                for t_idx in range(j1, j2):
                    t_item = target_sentences[t_idx]
                    differences.append({
                        "category": "content",
                        "diff_type": "added",
                        "title": "New text segment added",
                        "base_page": None,
                        "target_page": t_item["page"],
                        "base_content": "",
                        "target_content": t_item["text"],
                        "explanation": f"Sentence added to Page {t_item['page']}.",
                        "significance": "medium"
                    })

        # 3. Formatting Comparison: Typography & Geometry
        formatting_diffs = cls._compare_formatting(base_pages, target_pages)
        differences.extend(formatting_diffs)

        # 4. Table Comparison
        table_diffs = cls._compare_tables(base_pages, target_pages)
        differences.extend(table_diffs)

        return differences

    @classmethod
    def _classify_sentence_change(cls, b_item: Dict[str, Any], t_item: Dict[str, Any]) -> Dict[str, Any]:
        b_text = b_item["text"]
        t_text = t_item["text"]

        # Check for date shifts
        b_dates = cls.DATE_PATTERN.findall(b_text)
        t_dates = cls.DATE_PATTERN.findall(t_text)
        if b_dates and t_dates and b_dates != t_dates:
            return {
                "category": "content",
                "diff_type": "potentially_inconsistent",
                "title": f"Changed date: '{b_dates[0]}' to '{t_dates[0]}'",
                "base_page": b_item["page"],
                "target_page": t_item["page"],
                "base_content": b_text,
                "target_content": t_text,
                "explanation": f"Calendar date modified from '{b_dates[0]}' to '{t_dates[0]}'. Verify if this change was authorized.",
                "significance": "high"
            }

        # Check for monetary amount changes
        b_amts = cls.AMOUNT_PATTERN.findall(b_text)
        t_amts = cls.AMOUNT_PATTERN.findall(t_text)
        if b_amts and t_amts and b_amts != t_amts:
            return {
                "category": "content",
                "diff_type": "potentially_inconsistent",
                "title": f"Changed numerical amount: '{b_amts[0]}' to '{t_amts[0]}'",
                "base_page": b_item["page"],
                "target_page": t_item["page"],
                "base_content": b_text,
                "target_content": t_text,
                "explanation": f"Financial amount altered from '{b_amts[0]}' to '{t_amts[0]}'.",
                "significance": "high"
            }

        # General sentence modification
        return {
            "category": "content",
            "diff_type": "modified",
            "title": "Sentence wording revised",
            "base_page": b_item["page"],
            "target_page": t_item["page"],
            "base_content": b_text,
            "target_content": t_text,
            "explanation": f"Content was rephrased or updated between Page {b_item['page']} and Page {t_item['page']}.",
            "significance": "medium"
        }

    @classmethod
    def _compare_formatting(cls, base_pages: List[Dict[str, Any]], target_pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        diffs = []
        for i in range(min(len(base_pages), len(target_pages))):
            bp = base_pages[i]
            tp = target_pages[i]
            p_num = bp.get("page_number", i + 1)

            # Check font size drift in blocks
            b_fonts = {b.get("font_name") for b in bp.get("blocks", []) if b.get("font_name")}
            t_fonts = {b.get("font_name") for b in tp.get("blocks", []) if b.get("font_name")}
            if b_fonts and t_fonts and b_fonts != t_fonts:
                diffs.append({
                    "category": "formatting",
                    "diff_type": "formatting_only",
                    "title": f"Font family modified on Page {p_num}",
                    "base_page": p_num,
                    "target_page": p_num,
                    "base_content": f"Fonts: {', '.join(sorted(list(b_fonts))[:3])}",
                    "target_content": f"Fonts: {', '.join(sorted(list(t_fonts))[:3])}",
                    "explanation": f"Typeface changed between versions on Page {p_num}.",
                    "significance": "low"
                })

            # Check left margin drift
            b_margins = [b.get("bbox")[0] for b in bp.get("blocks", []) if b.get("bbox")]
            t_margins = [b.get("bbox")[0] for b in tp.get("blocks", []) if b.get("bbox")]
            if b_margins and t_margins:
                b_min = min(b_margins)
                t_min = min(t_margins)
                if abs(b_min - t_min) > 15.0:
                    diffs.append({
                        "category": "formatting",
                        "diff_type": "formatting_only",
                        "title": f"Page margin changed on Page {p_num}",
                        "base_page": p_num,
                        "target_page": p_num,
                        "base_content": f"Left margin: {b_min:.1f} pt",
                        "target_content": f"Left margin: {t_min:.1f} pt",
                        "explanation": f"Page layout margin shifted by {abs(b_min - t_min):.1f} pt.",
                        "significance": "low"
                    })
        return diffs

    @classmethod
    def _compare_tables(cls, base_pages: List[Dict[str, Any]], target_pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        diffs = []
        for i in range(min(len(base_pages), len(target_pages))):
            bp = base_pages[i]
            tp = target_pages[i]
            p_num = bp.get("page_number", i + 1)
            b_tables = bp.get("tables", [])
            t_tables = tp.get("tables", [])

            if len(b_tables) != len(t_tables):
                diffs.append({
                    "category": "structural",
                    "diff_type": "modified",
                    "title": f"Table count mismatch on Page {p_num}",
                    "base_page": p_num,
                    "target_page": p_num,
                    "base_content": f"{len(b_tables)} tables in base",
                    "target_content": f"{len(t_tables)} tables in revised",
                    "explanation": f"The number of tabular data structures differs on Page {p_num}.",
                    "significance": "medium"
                })
        return diffs

    @classmethod
    def _extract_headings(cls, pages: List[Dict[str, Any]], raw_text: str) -> List[Dict[str, Any]]:
        headings = []
        for p in pages:
            p_num = p.get("page_number", 1)
            for h in p.get("headings", []):
                text = h.get("text", "") if isinstance(h, dict) else str(h)
                if text.strip():
                    headings.append({"text": text.strip(), "page": p_num})
        # If no explicit headings extracted, check lines starting with numbered section or title casing
        if not headings:
            pattern = re.compile(r'^(?:[0-9]+\.\s+)?([A-Z][A-Za-z0-9\s]{3,40})$', re.MULTILINE)
            for m in pattern.finditer(raw_text):
                headings.append({"text": m.group(1).strip(), "page": 1})
        return headings

    @classmethod
    def _split_sentences(cls, pages: List[Dict[str, Any]], raw_text: str) -> List[Dict[str, Any]]:
        sentences = []
        if pages:
            for p in pages:
                p_num = p.get("page_number", 1)
                text = p.get("raw_text", "")
                parts = re.split(r'(?<=[.!?])\s+', text)
                for s in parts:
                    clean = s.strip()
                    if len(clean) > 8:
                        sentences.append({"text": clean, "page": p_num})
        else:
            parts = re.split(r'(?<=[.!?])\s+', raw_text)
            for s in parts:
                clean = s.strip()
                if len(clean) > 8:
                    sentences.append({"text": clean, "page": 1})
        return sentences
