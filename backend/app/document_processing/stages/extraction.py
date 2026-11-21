from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.core.exceptions import UnsupportedFileTypeError
from app.document_processing.extractors import PDFExtractor, DOCXExtractor, PPTXExtractor, OCRExtractor
from app.models.extraction_job import ExtractionJob
from app.models.extracted_page import ExtractedPage


class ExtractionStage:
    """
    Stage 2: Real Text and Structure Extraction
    Executes native PyMuPDF, python-docx, or python-pptx extraction on document bytes.
    Persists ExtractionJob and ExtractedPage records into PostgreSQL/SQLite when a database session is provided.
    """

    @classmethod
    async def process(
        cls,
        document_data: Dict[str, Any],
        file_bytes: bytes,
        db: Optional[Session] = None,
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        ext = document_data.get("extension", "").lower().replace(".", "")
        filename = document_data.get("filename", "unknown")
        logger.info(f"[Pipeline Stage 2: Extraction] Ingesting & extracting '{filename}' (format: .{ext})")

        job: Optional[ExtractionJob] = None
        if db and document_id:
            job = ExtractionJob(
                document_id=document_id,
                extractor_type=ext,
                status="processing",
                page_count=0
            )
            db.add(job)
            db.commit()
            db.refresh(job)

        try:
            if ext == "pdf":
                extracted = PDFExtractor.extract(file_bytes)
            elif ext == "docx":
                extracted = DOCXExtractor.extract(file_bytes)
            elif ext == "pptx":
                extracted = PPTXExtractor.extract(file_bytes)
            else:
                raise UnsupportedFileTypeError(extension=ext, allowed=["pdf", "docx", "pptx"])

            page_count = extracted.get("page_count", len(extracted.get("pages", [])))
            metadata = extracted.get("metadata", {})
            raw_text = extracted.get("raw_text", "")

            # Persist pages if DB is available
            if db and job:
                for p in extracted.get("pages", []):
                    s_data = p.get("structured_data", {})
                    if p.get("reconstructed_text"):
                        s_data["reconstructed_text"] = p.get("reconstructed_text")
                    page_record = ExtractedPage(
                        extraction_job_id=job.id,
                        page_number=p.get("page_number", 1),
                        raw_text=p.get("reconstructed_text") or p.get("raw_text", ""),
                        structured_data=s_data,
                        word_count=p.get("word_count", 0),
                        has_tables=p.get("has_tables", False),
                        extraction_method=p.get("extraction_method", "native"),
                        ocr_confidence=p.get("ocr_confidence"),
                        needs_ocr=p.get("needs_ocr", False),
                    )
                    db.add(page_record)

                job.status = "completed"
                job.page_count = page_count
                job.extraction_metadata = metadata
                db.commit()
                db.refresh(job)

            return {
                "status": "extracted",
                "job_id": job.id if job else None,
                "extractor_type": ext,
                "page_count": page_count,
                "metadata": metadata,
                "raw_text": raw_text,
                "pages": extracted.get("pages", []),
            }

        except Exception as e:
            logger.error(f"Extraction failed for {filename}: {e}", exc_info=True)
            if db and job:
                job.status = "failed"
                job.error_message = str(e)
                db.commit()

            return {
                "status": "failed",
                "job_id": job.id if job else None,
                "extractor_type": ext,
                "page_count": 0,
                "error": str(e),
                "metadata": {"error": str(e)},
                "raw_text": "",
                "pages": [],
            }
