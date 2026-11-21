from typing import Dict, Any, List
from app.core.logging import logger
from app.inspection_engine.consistency import EntityConsistencyInspector
from app.inspection_engine.table_validator import TableArithmeticValidator


class CrossFieldConsistencyStage:
    """
    Stage 6: Cross-Field and Cross-Document Consistency Validation
    Validates:
    - Inconsistent person and organization name spelling across pages.
    - Conflicting dates and chronological ordering for milestones.
    - Contradictions between narrative body text amounts and structured table totals.
    - Mathematical integrity of table columns with explicit stated totals (TableArithmeticValidator).
    """

    @classmethod
    async def process(cls, extraction_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        logger.info("[Pipeline Stage 6: Consistency] Running cross-page entity and numerical validation")
        findings: List[Dict[str, Any]] = []

        try:
            consistency_findings = EntityConsistencyInspector.inspect(extraction_data)
            findings.extend(consistency_findings)
        except Exception as e:
            logger.error(f"Error in EntityConsistencyInspector: {e}")

        try:
            table_findings = TableArithmeticValidator.inspect(extraction_data)
            findings.extend(table_findings)
        except Exception as e:
            logger.error(f"Error in TableArithmeticValidator: {e}")

        logger.info(f"[Pipeline Stage 6: Consistency] Detected {len(findings)} consistency and table arithmetic findings")
        return findings
