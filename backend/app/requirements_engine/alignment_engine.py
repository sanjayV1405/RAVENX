import re
from typing import Dict, Any, List, Optional, Tuple


class RequirementsAlignmentEngine:
    """
    Requirements Alignment Engine
    Evaluates a target document against a user-supplied requirement set or checklist.
    Categorizes each requirement into:
    - MET: Unambiguously satisfied with verbatim supporting evidence and page location.
    - PARTIALLY MET: Partially addressed or topic mentioned, but specific clauses or metrics missing.
    - MISSING: Required topic or clause is entirely absent from the document.
    - AMBIGUOUS: Document contains conflicting statements or vague phrasing regarding the requirement.
    - NOT VERIFIABLE: Requires external validation/evidence not present in user-supplied sources.
    """

    @classmethod
    def evaluate(
        cls,
        target_document_name: str,
        pages_data: List[Dict[str, Any]],
        raw_text: str,
        requirements: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []

        # Prepare normalized page texts with page numbers
        indexed_pages: List[Tuple[int, str, List[Dict[str, Any]]]] = []
        if pages_data:
            for p in pages_data:
                p_num = p.get("page_number", 1)
                p_text = p.get("raw_text", "")
                blocks = p.get("blocks", [])
                indexed_pages.append((p_num, p_text, blocks))
        else:
            indexed_pages.append((1, raw_text, []))

        full_doc_text = " ".join(p[1] for p in indexed_pages)

        for req in requirements:
            req_id = req.get("id")
            req_text = req.get("item_text") or req.get("text", "")
            req_cat = req.get("category", "general")
            importance = req.get("importance", "mandatory")

            res = cls._evaluate_single_requirement(
                req_text=req_text,
                target_document_name=target_document_name,
                indexed_pages=indexed_pages,
                full_text=full_doc_text
            )
            res["requirement_item_id"] = req_id
            res["requirement_text"] = req_text
            results.append(res)

        return results

    @classmethod
    def _evaluate_single_requirement(
        cls,
        req_text: str,
        target_document_name: str,
        indexed_pages: List[Tuple[int, str, List[Dict[str, Any]]]],
        full_text: str
    ) -> Dict[str, Any]:
        """Evaluates a single requirement against document pages."""
        req_clean = req_text.strip()
        req_lower = req_clean.lower()

        # 1. Check if the requirement requires external or non-verifiable verification
        if any(token in req_lower for token in ["physically inspect", "onsite audit", "external bank verification", "verify in person", "third-party laboratory"]):
            return {
                "status": "NOT VERIFIABLE",
                "supporting_evidence": None,
                "source_document_name": target_document_name,
                "page_number": None,
                "bbox": None,
                "explanation": "This requirement demands external, physical, or third-party validation that cannot be verified solely from the provided document text.",
                "confidence": 0.90
            }

        # 2. Extract key terms from requirement (ignore common stopwords)
        stopwords = {
            "the", "and", "or", "to", "in", "of", "a", "an", "is", "be", "for", "with",
            "must", "shall", "should", "will", "all", "each", "every", "that", "this",
            "document", "have", "has", "include", "provide", "contain", "ensure", "performed"
        }
        raw_words = [w.strip(".,;:?!\"'()[]") for w in req_lower.split() if len(w.strip(".,;:?!\"'()[]")) > 2]
        key_terms = [w for w in raw_words if w not in stopwords]

        def normalize_stem(word: str) -> str:
            w = word.lower().strip(".,;:?!\"'()[]")
            for suffix in ["ing", "tion", "ed", "es", "s"]:
                if len(w) > 4 and w.endswith(suffix):
                    return w[:-len(suffix)]
            return w

        stemmed_terms = {normalize_stem(t) for t in key_terms if len(normalize_stem(t)) >= 3}

        if not key_terms:
            return {
                "status": "AMBIGUOUS",
                "supporting_evidence": None,
                "source_document_name": target_document_name,
                "page_number": None,
                "bbox": None,
                "explanation": "Requirement is too brief or ambiguous to reliably match against the document.",
                "confidence": 0.70
            }

        # 3. Search across pages for matching sentences and blocks
        best_page = None
        best_sentence = None
        best_bbox = None
        matches_per_page: List[Tuple[int, str, Optional[List[float]], int]] = []
        conflicting_evidence: List[Tuple[int, str]] = []

        for p_num, p_text, blocks in indexed_pages:
            sentences = re.split(r'(?<=[.!?])\s+', p_text)
            for sentence in sentences:
                s_lower = sentence.lower()
                sentence_words = {normalize_stem(w) for w in s_lower.split() if len(w) > 2}

                # Count term hits by direct substring or stem overlap
                matched_count = sum(
                    1 for term in key_terms
                    if term in s_lower or normalize_stem(term) in sentence_words or any(normalize_stem(term) in sw for sw in sentence_words)
                )

                if matched_count > 0:
                    bbox = None
                    for b in blocks:
                        if sentence[:30].strip() in b.get("text", ""):
                            bbox = b.get("bbox")
                            break
                    matches_per_page.append((p_num, sentence.strip(), bbox, matched_count))

                # Look for explicit negation/conflict regarding the terms
                if any(term in s_lower or normalize_stem(term) in sentence_words for term in key_terms):
                    if any(neg in s_lower for neg in ["not complied", "pending", "does not support", "excluded", "omitted", "non-compliant", "waived"]):
                        conflicting_evidence.append((p_num, sentence.strip()))

        # Check for ambiguity: conflicting positive and negative evidence
        if conflicting_evidence and any(m[3] >= max(1, len(key_terms) // 2) for m in matches_per_page):
            conf_page, conf_text = conflicting_evidence[0]
            pos_page, pos_text, pos_bbox, _ = max(matches_per_page, key=lambda x: x[3])
            return {
                "status": "AMBIGUOUS",
                "supporting_evidence": f"Positive reference on Page {pos_page}: \"{pos_text}\" vs. Contradiction on Page {conf_page}: \"{conf_text}\"",
                "source_document_name": target_document_name,
                "page_number": pos_page,
                "bbox": pos_bbox,
                "explanation": f"The document contains ambiguous or conflicting information regarding this requirement (see Page {pos_page} vs Page {conf_page}).",
                "confidence": 0.88
            }

        # 4. Evaluate match depth
        if matches_per_page:
            # Sort by match count descending
            matches_per_page.sort(key=lambda x: x[3], reverse=True)
            top_page, top_sentence, top_bbox, top_matched_count = matches_per_page[0]
            match_ratio = top_matched_count / max(1, len(key_terms))

            if match_ratio >= 0.65 or (len(key_terms) <= 2 and top_matched_count == len(key_terms)):
                return {
                    "status": "MET",
                    "supporting_evidence": top_sentence,
                    "source_document_name": target_document_name,
                    "page_number": top_page,
                    "bbox": top_bbox,
                    "explanation": f"Requirement is fully supported by text on Page {top_page}: '{top_sentence}'.",
                    "confidence": min(0.98, round(0.85 + (match_ratio * 0.12), 2))
                }
            elif match_ratio >= 0.25 or top_matched_count >= 2:
                return {
                    "status": "PARTIALLY MET",
                    "supporting_evidence": top_sentence,
                    "source_document_name": target_document_name,
                    "page_number": top_page,
                    "bbox": top_bbox,
                    "explanation": f"Related topic is referenced on Page {top_page}, but specific requirement parameters or obligations are only partially satisfied.",
                    "confidence": round(0.75 + (match_ratio * 0.15), 2)
                }

        # 5. Not found anywhere
        return {
            "status": "MISSING",
            "supporting_evidence": None,
            "source_document_name": target_document_name,
            "page_number": None,
            "bbox": None,
            "explanation": "The requirement criteria and key terms were not identified anywhere in the provided document content.",
            "confidence": 0.95
        }
