import re
from typing import Dict, Any, List, Tuple, Optional
from app.core.logging import logger


class CorrectionVerificationLayer:
    """
    Phase 7: Pre-Correction Verification Layer.
    
    Before any accepted finding is permitted to modify a document:
    1. Rejects internal diagnostic and layout advice phrases from becoming document content.
    2. Validates that original content exists on the designated page/document.
    3. Detects duplicate, overlapping, or conflicting corrections.
    4. Ensures numerical and date corrections have verified structural evidence.
    5. Filters out non-actionable advisories (visual layout, structural hierarchy).
    6. Ensures meaning and document integrity are preserved.
    """

    # Phrases that indicate developer diagnostics or layout advice, NEVER valid document content
    DIAGNOSTIC_ADVISORY_PATTERNS = [
        re.compile(r'\badjust\s+(?:margin|container|bounds|spacing)\b', re.IGNORECASE),
        re.compile(r'\badd\s+(?:vertical|horizontal)?\s*spacing\b', re.IGNORECASE),
        re.compile(r'\bclear\s+floating\b', re.IGNORECASE),
        re.compile(r'\bdemote\s+to\s+h[1-6]\b', re.IGNORECASE),
        re.compile(r'\binsert\s+intervening\b', re.IGNORECASE),
        re.compile(r'\brenumber\s+section\b', re.IGNORECASE),
        re.compile(r'\bcheck\s+for\s+missing\b', re.IGNORECASE),
        re.compile(r'\bpopulate\s+table\b', re.IGNORECASE),
        re.compile(r'\bremove\s+blank\s+page\b', re.IGNORECASE),
        re.compile(r'\bdeskew\s+document\b', re.IGNORECASE),
        re.compile(r'\bstandardize\s+(?:on|corporate)\b', re.IGNORECASE),
        re.compile(r'\balign\s+(?:to|block)\b', re.IGNORECASE),
        re.compile(r'\bbring\s+text\s+within\s+printable\b', re.IGNORECASE),
        re.compile(r'\bexceeds?\s+page\s+boundaries\b', re.IGNORECASE),
    ]

    NON_ACTIONABLE_CATEGORIES = {"visual_layout", "structural"}
    NON_ACTIONABLE_CLASSIFICATIONS = {"B", "C"}  # B=uncertainty, C=visual/layout

    @classmethod
    def verify_findings(
        cls,
        findings: List[Dict[str, Any]],
        document_text_by_page: Optional[Dict[int, str]] = None
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Filters and validates accepted findings prior to correction execution.
        Returns:
            (verified_actionable_findings, rejected_or_suppressed_findings)
        """
        verified: List[Dict[str, Any]] = []
        rejected: List[Dict[str, Any]] = []
        claimed_spans: Dict[int, List[Tuple[str, str]]] = {}  # page -> [(original, replacement)]

        for f in findings:
            finding_id = f.get("id") or f.get("finding_id", "unknown")
            category = f.get("category", "")
            classification = f.get("finding_classification", "A")
            is_actionable = f.get("is_actionable", True)
            orig = f.get("original_content", "").strip()
            corr = f.get("suggested_correction", "").strip()
            page_num = f.get("page_number", 1)

            # 1. Non-actionable flag check
            if not is_actionable or category in cls.NON_ACTIONABLE_CATEGORIES or classification in cls.NON_ACTIONABLE_CLASSIFICATIONS:
                rejected.append({
                    "finding_id": finding_id,
                    "title": f.get("title"),
                    "verification_status": "NEEDS_REVIEW",
                    "reason": f"Category '{category}' / Classification '{classification}' is an advisory inspection note, not an actionable document edit."
                })
                continue

            # 2. Reject empty or identical pairs
            if not orig or not corr or orig == corr:
                rejected.append({
                    "finding_id": finding_id,
                    "title": f.get("title"),
                    "verification_status": "REJECTED",
                    "reason": "Original content and suggested correction are identical or empty."
                })
                continue

            # 3. Diagnostic text leak prevention
            if cls._is_diagnostic_advisory(corr):
                logger.warning(f"Blocked diagnostic text from document replacement: '{corr}'")
                rejected.append({
                    "finding_id": finding_id,
                    "title": f.get("title"),
                    "verification_status": "REJECTED",
                    "reason": f"Suggested correction '{corr}' contains advisory diagnostic instructions."
                })
                continue

            # 4. Check for meta-sentence wrappers in original content (e.g. 'Review Date: X vs Approval Date: Y')
            clean_orig, clean_corr = cls._sanitize_replacement_pair(orig, corr, f.get("title", ""))
            if not clean_orig or not clean_corr:
                rejected.append({
                    "finding_id": finding_id,
                    "title": f.get("title"),
                    "verification_status": "NEEDS_REVIEW",
                    "reason": "Could not determine precise target token pair from finding metadata."
                })
                continue

            # 5. Document text presence check (if text by page is supplied)
            if document_text_by_page and page_num in document_text_by_page:
                page_text = document_text_by_page[page_num]
                # Normalize spaces for verification
                norm_page = re.sub(r'\s+', ' ', page_text)
                norm_orig = re.sub(r'\s+', ' ', clean_orig)
                if norm_orig not in norm_page:
                    # Also check whole document in case page index shifted
                    all_text = " ".join(document_text_by_page.values())
                    norm_all = re.sub(r'\s+', ' ', all_text)
                    if norm_orig not in norm_all:
                        logger.warning(f"Target text '{clean_orig}' not found on page {page_num} or document body.")
                        rejected.append({
                            "finding_id": finding_id,
                            "title": f.get("title"),
                            "verification_status": "NEEDS_REVIEW",
                            "reason": f"Original text '{clean_orig}' was not located in document content."
                        })
                        continue

            # 6. Conflict & Overlap Detection
            if page_num not in claimed_spans:
                claimed_spans[page_num] = []

            has_conflict = False
            for prev_orig, prev_corr in claimed_spans[page_num]:
                # Exact target match with different replacement
                if prev_orig.lower() == clean_orig.lower() and prev_corr.lower() != clean_corr.lower():
                    has_conflict = True
                    rejected.append({
                        "finding_id": finding_id,
                        "title": f.get("title"),
                        "verification_status": "CONFLICT",
                        "reason": f"Conflicting correction on page {page_num}: already replacing '{prev_orig}' with '{prev_corr}'."
                    })
                    break

                # Substring overlap conflict: clean_orig inside prev_orig or vice versa
                if (clean_orig.lower() in prev_orig.lower() or prev_orig.lower() in clean_orig.lower()) and prev_orig.lower() != clean_orig.lower():
                    has_conflict = True
                    rejected.append({
                        "finding_id": finding_id,
                        "title": f.get("title"),
                        "verification_status": "CONFLICT",
                        "reason": f"Overlapping span conflict on page {page_num}: '{clean_orig}' overlaps with previously scheduled correction '{prev_orig}'."
                    })
                    break

            if has_conflict:
                continue

            # 7. Verified! Package clean finding
            claimed_spans[page_num].append((clean_orig, clean_corr))
            verified_item = dict(f)
            verified_item["original_content"] = clean_orig
            verified_item["suggested_correction"] = clean_corr
            verified_item["verification_status"] = "VERIFIED"
            verified.append(verified_item)

        logger.info(f"[CorrectionVerificationLayer] {len(verified)} findings verified for execution, {len(rejected)} advisories/conflicts filtered out.")
        return verified, rejected

    @classmethod
    def _is_diagnostic_advisory(cls, text: str) -> bool:
        """Returns True if the text contains instructional advice keywords rather than document prose."""
        for pattern in cls.DIAGNOSTIC_ADVISORY_PATTERNS:
            if pattern.search(text):
                return True
        return False

    @classmethod
    def _sanitize_replacement_pair(cls, orig: str, corr: str, title: str) -> Tuple[str, str]:
        """Ensures that replacement pair consists of pure text tokens without meta-phrases."""
        # 1. Table arithmetic: "Update stated total from 138 to calculated sum 128"
        table_match = re.search(r'from\s+([0-9,]+(?:\.[0-9]+)?)\s+to\s+calculated\s+sum\s+([0-9,]+(?:\.[0-9]+)?)', corr, re.IGNORECASE)
        if table_match:
            return table_match.group(1), table_match.group(2)

        # 2. Chronological date: "Review Date: '30 June 2026' vs Approval Date: '12 June 2026'"
        if "approval date" in title.lower() or "chronological" in title.lower():
            date_match = re.search(r'approval date:\s*\'([^\']+)\'', orig, re.IGNORECASE)
            sugg_date_match = re.search(r'\(([0-9]{1,2}\s+[A-Za-z]+\s+20[2-3][0-9])\)', corr)
            if date_match and sugg_date_match:
                return date_match.group(1), sugg_date_match.group(1)

        # 3. Organization variant meta-phrase: "'North Star' (Page [1]) vs 'Northstar' (Page [2])"
        if "organization" in title.lower():
            org_match = re.search(r"'([^']+)'\s*\(Page[^)]+\)\s*vs\s*'([^']+)'", orig)
            if org_match:
                return org_match.group(2), org_match.group(1)

        # 4. Standard direct replacement
        return orig.strip(), corr.strip()
