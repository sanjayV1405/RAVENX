from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ComparisonDifferenceResponse(BaseModel):
    id: str
    comparison_id: str
    category: str  # content, structural, formatting
    diff_type: str  # added, removed, modified, potentially_inconsistent, formatting_only
    title: str
    base_page: Optional[int] = None
    target_page: Optional[int] = None
    base_content: Optional[str] = None
    target_content: Optional[str] = None
    explanation: str
    significance: str  # high, medium, low
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentComparisonCreate(BaseModel):
    base_document_id: str = Field(..., description="UUID of the original reference document")
    target_document_id: str = Field(..., description="UUID of the revised target document")


class DocumentComparisonResponse(BaseModel):
    id: str
    base_document_id: str
    target_document_id: str
    status: str
    summary: Optional[Dict[str, int]] = None
    differences: List[ComparisonDifferenceResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

