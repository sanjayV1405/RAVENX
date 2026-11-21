from typing import Dict, Any, List
from app.core.logging import logger
from app.inspection_engine.micro_typography import MicroTypographyInspector
from app.inspection_engine.grammar import GrammarInspector


class GrammarInspectionStage:
    """
    Stage 3: Micro-Typographical and Grammar Inspection
    Executes:
    - MicroTypographyInspector (missing/extra spaces, place-name+number concatenations, repeated words, typos, leetspeak, punctuation errors).
    - GrammarInspector (subject-verb agreement, verb forms, article misuse, sentence capitalization, domain allowlisting).
    """

    @classmethod
    async def process(cls, extraction_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        logger.info("[Pipeline Stage 3: Grammar] Running micro-typography and language inspection engines")
        findings: List[Dict[str, Any]] = []

        try:
            typo_findings = MicroTypographyInspector.inspect(extraction_data)
            findings.extend(typo_findings)
        except Exception as e:
            logger.error(f"Error in MicroTypographyInspector: {e}")

        try:
            grammar_findings = GrammarInspector.inspect(extraction_data)
            findings.extend(grammar_findings)
        except Exception as e:
            logger.error(f"Error in GrammarInspector: {e}")

        logger.info(f"[Pipeline Stage 3: Grammar] Detected {len(findings)} micro-typographical and grammar findings")
        return findings
