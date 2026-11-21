from typing import Dict, Any, List
from app.core.logging import logger


class FindingDeduplicationStage:
    """
    Stage 7: Finding Validation & Deduplication
    Performs:
    - Merges overlapping findings across rule-based engines and contextual AI models.
    - Resolves confidence scoring and removes duplicate flags.
    - Normalizes severity ratings (critical, high, medium, low, info).
    - Ensures evidence grounding and attaches user review default status.
    """

    VALID_SEVERITIES = {"critical", "high", "medium", "low", "info"}

    @classmethod
    async def process(cls, raw_findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        logger.info(f"[Pipeline Stage 7: Deduplication] Normalizing and deduplicating {len(raw_findings)} raw findings")
        unique_findings: List[Dict[str, Any]] = []
        seen_signatures = set()

        for item in raw_findings:
            category = item.get("category", "general")
            page_num = item.get("page_number", 1)
            orig = item.get("original_content", "").strip()
            corr = item.get("suggested_correction", "").strip()
            classification = item.get("finding_classification", "A")

            if not orig:
                continue

            # Determine if this finding is actionable text replacement or advisory only
            is_actionable = item.get("is_actionable", True)
            if category in ("visual_layout", "structural") or classification in ("B", "C"):
                is_actionable = False

            # Signature key based on category, page, and lowercased content
            sig = (
                category,
                page_num,
                orig.lower(),
                corr.lower()
            )

            if sig in seen_signatures:
                continue
            seen_signatures.add(sig)

            # Normalize severity
            sev = item.get("severity", "medium").lower()
            if sev not in cls.VALID_SEVERITIES:
                sev = "medium"

            # Normalize confidence
            conf = float(item.get("confidence", 0.9))
            conf = max(0.1, min(1.0, conf))

            unique_findings.append({
                "category": category,
                "title": item.get("title", "Detected Document Anomaly"),
                "finding_classification": classification,
                "is_actionable": is_actionable,
                "page_number": page_num,
                "original_content": orig,
                "suggested_correction": corr,
                "explanation": item.get("explanation", ""),
                "severity": sev,
                "confidence": round(conf, 2),
                "evidence_source": item.get("evidence_source", "deterministic_rule"),
                "bbox": item.get("bbox"),
                "char_offset_start": item.get("char_offset_start"),
                "char_offset_end": item.get("char_offset_end"),
                "detection_method": item.get("detection_method", "rule_based"),
                "user_status": "needs_review"
            })

        logger.info(f"[Pipeline Stage 7: Deduplication] Deduplication completed: {len(unique_findings)} distinct findings retained")
        return unique_findings
