from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class CorrectedDocumentResponse(BaseModel):
    id: str
    inspection_id: str
    document_id: str
    original_filename: str
    corrected_filename: str
    file_extension: str
    file_size_bytes: int
    checksum: Optional[str] = None
    applied_findings_count: int
    correction_summary: Optional[Dict[str, Any]] = None
    download_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ApplyCorrectionRequest(BaseModel):
    selected_finding_ids: Optional[List[str]] = Field(
        None,
        description="Optional list of specific finding IDs to accept and apply. If omitted, all accepted findings are applied."
    )
