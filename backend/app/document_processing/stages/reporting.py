from typing import Dict, Any, List
from app.core.logging import logger


class ReportGenerationStage:
    """
    Stage 8: Report Generation
    Produces:
    - Comprehensive inspection audit reports.
    - Severity breakdown summaries.
    - Exportable metadata.
    """

    @classmethod
    async def process(cls, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        logger.info(f"[Pipeline Stage 8: Reporting] Compiling inspection summary for {len(findings)} findings")
        summary = {
            "total_findings": len(findings),
            "critical_severity": 0,
            "high_severity": 0,
            "medium_severity": 0,
            "low_severity": 0,
            "info_severity": 0,
        }

        for f in findings:
            sev = f.get("severity", "medium").lower()
            key = f"{sev}_severity"
            if key in summary:
                summary[key] += 1
            else:
                summary["medium_severity"] += 1

        return {
            "summary": summary,
            "findings_count": len(findings),
            "status": "completed"
        }

