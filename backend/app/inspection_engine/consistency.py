import re
from typing import Dict, Any, List, Optional, Tuple, Set
from collections import defaultdict
from datetime import datetime


def levenshtein_distance(s1: str, s2: str) -> int:
    """Computes basic Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


class EntityConsistencyInspector:
    """
    Module C: Entity Consistency Validation Engine
    Extracts and cross-compares:
    - Person names across pages and sections.
    - Dates associated with key project/document milestones (including chronological sequence).
    - Monetary amounts between narrative body text and structured tables (including Indian numbering).
    - Organization and institution names (detecting spelling drifts like 'North Star' vs 'Northstar').
    - Identifies spelling drifts, date discrepancies, and numerical mismatches.

    Classifications:
    - A: Direct source document issue
    - D: Contextual / Cross-entity inconsistency
    """

    # Honorifics used to identify person names
    HONORIFICS = ["Dr\\.", "Mr\\.", "Mrs\\.", "Ms\\.", "Prof\\.", "Doctor", "Professor"]
    HONORIFIC_PATTERN = re.compile(
        rf'\b({"|".join(HONORIFICS)})\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
    )

    # Date patterns (ISO, Month Day Year, Day Month Year, Slash/Dash format)
    DATE_PATTERNS = [
        re.compile(r'\b(20[2-3][0-9]-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01]))\b'),  # YYYY-MM-DD
        re.compile(r'\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+(?:[1-9]|[12][0-9]|3[01]),\s+20[2-3][0-9])\b', re.IGNORECASE),
        re.compile(r'\b((?:[1-9]|[12][0-9]|3[01])(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+20[2-3][0-9])\b', re.IGNORECASE),
        re.compile(r'\b((?:0[1-9]|1[0-2])/(?:0[1-9]|[12][0-9]|3[01])/20[2-3][0-9])\b'),
    ]

    # Monetary amounts pattern ($1,234.56, €500,000, USD 45,000, ₹3,20,000, I22,500, ·8,50,000, etc.)
    AMOUNT_PATTERN = re.compile(
        r'\b(?:USD|EUR|GBP|CAD|AUD|\$|€|£|₹|Rs\.?|[I·])\s?([0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]{2})?)\b'
    )

    # Organization patterns with proper capitalized entity names (Title Case or UPPERCASE)
    ORG_SUFFIX_PATTERN = re.compile(
        r'\b([A-Z][a-zA-Z0-9]*(?:\s+[A-Z][a-zA-Z0-9]*)*\s+(?:[Oo]ffice [Ss]ystems|[Ss]ystems|[Cc]orporation|[Cc]orp|[Ii]nc|[Ll]td|[Ll]imited|[Tt]echnologies|[Gg]roup|[Ss]olutions|[Ee]nterprises|OFFICE SYSTEMS|SYSTEMS|CORPORATION|CORP|INC|LTD|LIMITED|TECHNOLOGIES|GROUP|SOLUTIONS|ENTERPRISES))\b'
    )

    @classmethod
    def _parse_date(cls, date_str: str) -> Optional[datetime]:
        """Tries to parse standard date representations."""
        formats = [
            "%d %B %Y", "%d %b %Y",
            "%B %d, %Y", "%b %d, %Y",
            "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"
        ]
        # Remove ordinal suffixes (1st, 2nd, 3rd, 12th)
        cleaned = re.sub(r'(?<=\d)(st|nd|rd|th)', '', date_str.strip())
        for fmt in formats:
            try:
                return datetime.strptime(cleaned, fmt)
            except ValueError:
                continue
        return None

    @classmethod
    def inspect(cls, extraction_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        findings: List[Dict[str, Any]] = []
        pages = extraction_data.get("pages", [])

        # Data stores indexed by page
        person_names_by_page: Dict[str, Set[int]] = defaultdict(set)
        dates_by_page: Dict[str, Set[int]] = defaultdict(set)
        org_names_by_page: Dict[str, Set[int]] = defaultdict(set)
        org_counts: Dict[str, int] = defaultdict(int)
        amounts_in_text: Dict[str, Set[int]] = defaultdict(set)
        milestones: Dict[str, Tuple[datetime, str, int]] = {}

        # 1. Harvest entities across pages
        for page in pages:
            page_num = page.get("page_number", 1)
            raw_text = page.get("reconstructed_text") or page.get("raw_text", "")

            # Person names with honorifics
            for match in cls.HONORIFIC_PATTERN.finditer(raw_text):
                full_name = f"{match.group(1)} {match.group(2)}"
                person_names_by_page[full_name].add(page_num)

            # Dates
            for dp in cls.DATE_PATTERNS:
                for match in dp.finditer(raw_text):
                    dates_by_page[match.group(1)].add(page_num)

            # Milestone date extraction: e.g. "Review date: 30 June 2026", "Approval date: 12 June 2026"
            ms_pattern = re.compile(
                r'\b(review date|approval date|effective date|audit date|completion date|submission date)[:\s]+([0-9]{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+20[2-3][0-9]|[A-Za-z]+\s+[0-9]{1,2},\s+20[2-3][0-9]|20[2-3][0-9]-[0-9]{2}-[0-9]{2})\b',
                re.IGNORECASE
            )
            for ms_match in ms_pattern.finditer(raw_text):
                ms_key = ms_match.group(1).lower().strip()
                ms_raw = ms_match.group(2).strip()
                parsed = cls._parse_date(ms_raw)
                if parsed:
                    milestones[ms_key] = (parsed, ms_raw, page_num)

            # Document Identifier extraction: e.g. "DocuMent ID: NOS-OPS-Q2-026", "Document ID: DOC-99"
            doc_id_pattern = re.compile(
                r'\b(?:document|report|doc|contract|policy|project)\s*id[:\s]+([A-Z0-9_\-]+)\b',
                re.IGNORECASE
            )
            for did_match in doc_id_pattern.finditer(raw_text):
                did_val = did_match.group(1).strip()
                if len(did_val) >= 4 and not did_val.isdigit():
                    amounts_in_text[f"__DOC_ID__:{did_val}"].add(page_num)

            # Organization names
            for org_match in cls.ORG_SUFFIX_PATTERN.finditer(raw_text):
                org_name = org_match.group(1).strip()
                if len(org_name.split()) >= 2:
                    org_names_by_page[org_name].add(page_num)
                    org_counts[org_name] += 1

            # Amounts in body text
            for match in cls.AMOUNT_PATTERN.finditer(raw_text):
                amount_str = match.group(0)
                amounts_in_text[amount_str].add(page_num)

        # 2. Check Person Name Spelling Inconsistencies
        names = list(person_names_by_page.keys())
        checked_pairs: Set[Tuple[str, str]] = set()

        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                n1, n2 = names[i], names[j]
                pair_key = (min(n1, n2), max(n1, n2))
                if pair_key in checked_pairs:
                    continue
                checked_pairs.add(pair_key)

                h1 = n1.split()[0]
                h2 = n2.split()[0]
                if h1 == h2:
                    name_body1 = " ".join(n1.split()[1:])
                    name_body2 = " ".join(n2.split()[1:])
                    dist = levenshtein_distance(name_body1.lower(), name_body2.lower())
                    if 1 <= dist <= 2 and len(name_body1) > 5 and len(name_body2) > 5:
                        p1_list = sorted(list(person_names_by_page[n1]))
                        p2_list = sorted(list(person_names_by_page[n2]))
                        findings.append({
                            "category": "entity_consistency",
                            "title": "Inconsistent person name spelling across document",
                            "finding_classification": "A",
                            "is_actionable": False,  # Cross-reference advisory
                            "page_number": p2_list[0] if p2_list else 1,
                            "original_content": f"'{n1}' on Page {p1_list} vs '{n2}' on Page {p2_list}",
                            "suggested_correction": f"Standardize on either '{n1}' or '{n2}' consistently",
                            "explanation": f"The individual is referred to as '{n1}' on page {p1_list} and '{n2}' on page {p2_list}. This single-letter discrepancy is an unverified name variation.",
                            "severity": "high",
                            "confidence": 0.89,
                            "evidence_source": "entity_consistency_engine",
                            "bbox": None,
                            "detection_method": "cross_reference"
                        })

        # 3. Check Organization Name Variants with Majority Voting
        org_list = list(org_names_by_page.keys())
        checked_orgs: Set[Tuple[str, str]] = set()
        for i in range(len(org_list)):
            for j in range(i + 1, len(org_list)):
                o1, o2 = org_list[i], org_list[j]
                pair_key = (min(o1, o2), max(o1, o2))
                if pair_key in checked_orgs:
                    continue
                checked_orgs.add(pair_key)

                # Normalized comparison without spaces and casing, or 1-2 char spelling drift
                norm1 = re.sub(r'\s+', '', o1).lower()
                norm2 = re.sub(r'\s+', '', o2).lower()
                is_drift = False
                if norm1 == norm2 and o1.lower() != o2.lower():
                    is_drift = True
                elif 1 <= levenshtein_distance(o1.lower(), o2.lower()) <= 2:
                    is_drift = True

                if is_drift:
                    # Majority voting: select the more frequently occurring variant as canonical
                    count1 = org_counts.get(o1, 1)
                    count2 = org_counts.get(o2, 1)
                    if count1 >= count2:
                        canonical = o1
                        variant = o2
                        target_pages = sorted(list(org_names_by_page[o2]))
                    else:
                        canonical = o2
                        variant = o1
                        target_pages = sorted(list(org_names_by_page[o1]))

                    for p_num in target_pages:
                        findings.append({
                            "category": "entity_consistency",
                            "title": f"Inconsistent organization name styling ('{variant}')",
                            "finding_classification": "A",
                            "is_actionable": True,
                            "page_number": p_num,
                            "original_content": variant,
                            "suggested_correction": canonical,
                            "explanation": f"The entity is written as '{variant}' on page {p_num}, but the standard representation throughout the document is '{canonical}'.",
                            "severity": "high",
                            "confidence": 0.95,
                            "evidence_source": "entity_consistency_engine",
                            "bbox": None,
                            "detection_method": "cross_reference"
                        })

        # 4. Check Chronological Milestone Contradictions (e.g. Approval Date < Review Date)
        if "approval date" in milestones and "review date" in milestones:
            app_dt, app_raw, app_pg = milestones["approval date"]
            rev_dt, rev_raw, rev_pg = milestones["review date"]
            if app_dt < rev_dt:
                findings.append({
                    "category": "consistency",
                    "title": "Chronological inconsistency: Approval date precedes review date",
                    "finding_classification": "D",  # Contextual logic contradiction
                    "is_actionable": True,
                    "page_number": app_pg,
                    "original_content": app_raw,
                    "suggested_correction": rev_raw,
                    "explanation": f"Formal document approval date ({app_raw}) cannot chronologically precede the review completion date ({rev_raw}). Suggested alignment to review completion date.",
                    "severity": "critical",
                    "confidence": 0.98,
                    "evidence_source": "entity_consistency_engine",
                    "bbox": None,
                    "detection_method": "cross_reference"
                })

        # 5. Check for Date Conflicts if duplicate milestone labels exist with different dates
        for page in pages:
            page_num = page.get("page_number", 1)
            raw_text = page.get("reconstructed_text") or page.get("raw_text", "")
            effective_matches = list(re.finditer(r'(effective date|completion date|deadline|due date)[:\s]+([^\n.,;]+)', raw_text, re.IGNORECASE))
            if effective_matches:
                for match in effective_matches:
                    label = match.group(1).title()
                    date_val = match.group(2).strip()
                    for other_page in pages:
                        other_page_num = other_page.get("page_number", 1)
                        if other_page_num <= page_num:
                            continue
                        other_text = other_page.get("reconstructed_text") or other_page.get("raw_text", "")
                        for other_match in re.finditer(rf'({re.escape(label)})[:\s]+([^\n.,;]+)', other_text, re.IGNORECASE):
                            other_date_val = other_match.group(2).strip()
                            if date_val.lower() != other_date_val.lower():
                                findings.append({
                                    "category": "entity_consistency",
                                    "title": f"Conflicting {label} across pages",
                                    "finding_classification": "D",
                                    "page_number": other_page_num,
                                    "original_content": f"{label}: '{other_date_val}' (Page {other_page_num}) vs '{date_val}' (Page {page_num})",
                                    "suggested_correction": f"Align {label} to a single agreed date",
                                    "explanation": f"Discrepancy detected for {label}: '{date_val}' is stated on page {page_num}, but '{other_date_val}' is stated on page {other_page_num}.",
                                    "severity": "critical",
                                    "confidence": 0.95,
                                    "evidence_source": "entity_consistency_engine",
                                    "bbox": None,
                                    "detection_method": "cross_reference"
                                })

        # 6. Check for Document Identifier Inconsistencies across pages
        doc_ids = [k.replace("__DOC_ID__:", "") for k in amounts_in_text.keys() if k.startswith("__DOC_ID__:")]
        if len(doc_ids) >= 2:
            for i in range(len(doc_ids)):
                for j in range(i + 1, len(doc_ids)):
                    id1 = doc_ids[i]
                    id2 = doc_ids[j]
                    dist = levenshtein_distance(id1, id2)
                    if 1 <= dist <= 2:
                        # Variant detected
                        pg1 = sorted(list(amounts_in_text[f"__DOC_ID__:{id1}"]))[0]
                        pg2 = sorted(list(amounts_in_text[f"__DOC_ID__:{id2}"]))[0]
                        findings.append({
                            "category": "entity_consistency",
                            "title": f"Inconsistent document identifier '{id2}' vs '{id1}'",
                            "finding_classification": "D",
                            "is_actionable": True,
                            "page_number": pg2,
                            "original_content": id2,
                            "suggested_correction": id1,
                            "explanation": f"Document ID is stated as '{id1}' on page {pg1}, but appears as '{id2}' on page {pg2}.",
                            "severity": "high",
                            "confidence": 0.94,
                            "evidence_source": "entity_consistency_engine",
                            "bbox": None,
                            "detection_method": "cross_reference"
                        })

        # 7. Narrative Financial Variance / Overrun Discrepancy
        for page in pages:
            page_num = page.get("page_number", 1)
            raw_text = page.get("reconstructed_text") or page.get("raw_text", "")
            
            variance_pattern = re.compile(
                r'(?:approved|operating|project|allocated)\s+(?:operating\s+)?budget\s+(?:for\s+[^.]+?)?was\s+([I₹$€£·]|Rs\.?)?\s*([0-9,]+(?:\.[0-9]+)?).*?'
                r'actual\s+(?:operating\s+)?expenditure\s+(?:for\s+[^.]+?)?was\s+([I₹$€£·]|Rs\.?)?\s*([0-9,]+(?:\.[0-9]+)?).*?'
                r'(?:resulting\s+in\s+an?\s+)?overrun\s+of\s+([I₹$€£·]|Rs\.?)?\s*([0-9,]+(?:\.[0-9]+)?)',
                re.IGNORECASE | re.DOTALL
            )
            for m in variance_pattern.finditer(raw_text):
                curr_symbol = m.group(1) or m.group(3) or m.group(5) or "₹"
                if curr_symbol in ("I", "·"):
                    curr_symbol = "₹"

                budget_str = m.group(2).rstrip(',')
                actual_str = m.group(4).rstrip(',')
                stated_overrun_str = m.group(6).rstrip(',')

                try:
                    budget_val = float(budget_str.replace(",", ""))
                    actual_val = float(actual_str.replace(",", ""))
                    stated_overrun_val = float(stated_overrun_str.replace(",", ""))
                except ValueError:
                    continue

                calc_overrun_val = actual_val - budget_val
                if abs(calc_overrun_val - stated_overrun_val) > 0.01:
                    # Format calculated overrun in Indian numbering or standard comma format
                    s_int = str(int(calc_overrun_val))
                    if len(s_int) > 3:
                        last3 = s_int[-3:]
                        rest = s_int[:-3]
                        parts = []
                        while len(rest) > 2:
                            parts.insert(0, rest[-2:])
                            rest = rest[:-2]
                        if rest:
                            parts.insert(0, rest)
                        calc_str = ",".join(parts) + "," + last3
                    else:
                        calc_str = s_int

                    diff_val = abs(calc_overrun_val - stated_overrun_val)
                    diff_str = f"{int(diff_val):,}" if diff_val.is_integer() else f"{diff_val:,.2f}"

                    prefix = m.group(5) or ""
                    orig_token = f"{prefix}{stated_overrun_str}"
                    corr_token = f"{curr_symbol}{calc_str}" if prefix else calc_str

                    findings.append({
                        "category": "consistency",
                        "title": "Financial calculation discrepancy: reported budget overrun mismatch",
                        "finding_classification": "A",
                        "is_actionable": True,
                        "page_number": page_num,
                        "original_content": orig_token,
                        "suggested_correction": corr_token,
                        "explanation": f"Approved budget of {curr_symbol}{budget_str} and actual expenditure of {curr_symbol}{actual_str} results in a calculated overrun of {curr_symbol}{calc_str} ({curr_symbol}{actual_str} - {curr_symbol}{budget_str}), differing from stated {curr_symbol}{stated_overrun_str} by {curr_symbol}{diff_str}. Explicit approval is required before applying.",
                        "severity": "critical",
                        "confidence": 0.99,
                        "evidence_source": "financial_variance_engine",
                        "bbox": None,
                        "detection_method": "arithmetic_verification"
                    })

        return findings
