from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ExtractionJobResponse(BaseModel):
    id: str
    document_id: str
    status: str
    extractor_type: str
    page_count: int
    error_message: Optional[str] = None
    extraction_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExtractedPageSummary(BaseModel):
    id: str
    extraction_job_id: str
    page_number: int
    word_count: int
    has_tables: bool
    extraction_method: str
    needs_ocr: bool
    ocr_confidence: Optional[float] = None
    preview_snippet: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ExtractedPageDetail(BaseModel):
    id: str
    extraction_job_id: str
    page_number: int
    raw_text: Optional[str] = ""
    structured_data: Optional[Dict[str, Any]] = None
    word_count: int
    has_tables: bool
    extraction_method: str
    needs_ocr: bool
    ocr_confidence: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    file_extension: str
    file_size_bytes: int
    mime_type: str
    storage_path: str
    checksum: Optional[str] = None
    page_count: Optional[int] = None
    status: str
    is_duplicate: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

