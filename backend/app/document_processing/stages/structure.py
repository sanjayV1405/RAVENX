from typing import Dict, Any, List
from app.core.logging import logger
from app.inspection_engine.structure import DocumentStructureInspector


class DocumentStructureInspectionStage:
    """
    Stage: Document Structure and Section Hierarchy Inspection
    Detects:
    - Skipped heading hierarchy (H1 -> H3).
    - Broken numbering sequences in numbered sections.
    - Empty unpopulated tables.
    - Unexpected blank pages inside document body.
    """

    @classmethod
    async def process(cls, extraction_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        logger.info("[Pipeline Stage: Structure] Inspecting document hierarchy and organizational flow")
        findings: List[Dict[str, Any]] = []

        try:
            struct_findings = DocumentStructureInspector.inspect(extraction_data)
            findings.extend(struct_findings)
        except Exception as e:
            logger.error(f"Error in DocumentStructureInspector: {e}")

        logger.info(f"[Pipeline Stage: Structure] Detected {len(findings)} structural findings")
        return findings

