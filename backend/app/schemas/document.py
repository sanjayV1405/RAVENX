from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class DocumentBase(BaseModel):
    filename: str
    file_extension: str
    file_size_bytes: int
    mime_type: str


class DocumentCreate(DocumentBase):
    storage_path: str
    checksum: Optional[str] = None


class DocumentResponse(DocumentBase):
    id: str
    storage_path: str
    checksum: Optional[str] = None
    page_count: Optional[int] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

