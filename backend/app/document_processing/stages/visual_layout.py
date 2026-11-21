from typing import Dict, Any, List
from app.core.logging import logger
from app.inspection_engine.visual_layout import VisualLayoutInspector


class VisualLayoutInspectionStage:
    """
    Stage 4: Visual Layout and Geometry Inspection
    Detects:
    - Text blocks exceeding printable page boundaries.
    - Overlapping/colliding text elements.
    - Severe margin drift across consecutive text blocks.
    - Skew and rotational misalignment using OpenCV contour analysis.
    """

    @classmethod
    async def process(cls, extraction_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        logger.info("[Pipeline Stage 4: Visual Layout] Inspecting document geometry and layout bounds")
        findings: List[Dict[str, Any]] = []

        try:
            layout_findings = VisualLayoutInspector.inspect(extraction_data)
            findings.extend(layout_findings)
        except Exception as e:
            logger.error(f"Error in VisualLayoutInspector: {e}")

        logger.info(f"[Pipeline Stage 4: Visual Layout] Detected {len(findings)} visual layout findings")
        return findings
