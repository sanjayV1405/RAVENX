from typing import Dict, Any, List, Optional
from app.document_processing.stages import (
    IngestionStage,
    ExtractionStage,
    GrammarInspectionStage,
    VisualLayoutInspectionStage,
    ContextualAIInspectionStage,
    CrossFieldConsistencyStage,
    DocumentStructureInspectionStage,
    FindingDeduplicationStage,
    ReportGenerationStage,
)
from app.core.logging import logger


class DocumentInspectionPipeline:
    """
    Modular Multi-Stage Document Inspection Pipeline for RAVENX AI.
    Combines:
    - Ingestion and Format Validation
    - Deep Extraction (PDF, DOCX, PPTX)
    - Micro-Typographical and Grammar Inspection
    - Visual Layout and Spatial Geometry Inspection
    - Contextual AI Analysis (DeepSeek / Gemini with fallback)
    - Cross-Field and Cross-Page Entity Consistency
    - Structural and Section Hierarchy Validation
    - Finding Deduplication, Normalization and Grounding
    - Comprehensive Audit Report Generation
    """

    def __init__(self, ai_provider: str = "deepseek"):
        self.ai_provider = ai_provider

    async def execute(
        self,
        filename: str,
        file_bytes: bytes,
        guidelines: Optional[str] = None,
        db: Optional[Any] = None,
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        logger.info(f"Starting pipeline execution for: {filename}")

        # Stage 1: Ingestion & Validation
        ingestion_result = await IngestionStage.process(filename, file_bytes)

        # Stage 2: Text and structure extraction
        extraction_result = await ExtractionStage.process(
            document_data=ingestion_result,
            file_bytes=file_bytes,
            db=db,
            document_id=document_id
        )
        if extraction_result.get("status") == "failed":
            from app.core.exceptions import InspectionStageError
            raise InspectionStageError("ExtractionStage", extraction_result.get("error", "Extraction failed"))

        # Stage 3: Grammar & micro-typographical inspection
        grammar_findings = await GrammarInspectionStage.process(extraction_result)

        # Stage 4: Visual layout and geometry inspection
        layout_findings = await VisualLayoutInspectionStage.process(extraction_result)

        # Stage 5: Contextual AI inspection (DeepSeek / Gemini)
        ai_findings = await ContextualAIInspectionStage.process(
            extraction_result,
            ai_provider_name=self.ai_provider,
            guidelines=guidelines
        )

        # Stage 6: Cross-field consistency validation
        consistency_findings = await CrossFieldConsistencyStage.process(extraction_result)

        # Stage: Structural hierarchy and section sequence inspection
        structural_findings = await DocumentStructureInspectionStage.process(extraction_result)

        # Stage 7: Finding validation, grounding and deduplication
        raw_findings = grammar_findings + layout_findings + ai_findings + consistency_findings + structural_findings
        deduplicated_findings = await FindingDeduplicationStage.process(raw_findings)

        # Stage 8: Report generation
        report_result = await ReportGenerationStage.process(deduplicated_findings)

        return {
            "ingestion": ingestion_result,
            "extraction": extraction_result,
            "findings": deduplicated_findings,
            "report": report_result,
        }

