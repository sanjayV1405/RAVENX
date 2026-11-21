from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class RequirementItemCreate(BaseModel):
    item_text: str = Field(..., description="The clause or rule text to evaluate")
    category: Optional[str] = Field("general", description="Category or clause type")
    importance: Optional[str] = Field("mandatory", description="mandatory, recommended, optional")


class RequirementItemResponse(RequirementItemCreate):
    id: str
    requirement_set_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class RequirementSetCreate(BaseModel):
    title: str = Field(..., description="Title of the requirement set")
    description: Optional[str] = Field(None, description="Detailed description")
    source_type: Optional[str] = Field("manual", description="manual, checklist, reference_doc")
    reference_document_id: Optional[str] = None
    items: List[RequirementItemCreate] = []


class RequirementSetResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    source_type: str
    reference_document_id: Optional[str] = None
    items: List[RequirementItemResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RequirementResultResponse(BaseModel):
    id: str
    requirement_item_id: Optional[str] = None
    requirement_text: str
    status: str  # MET, PARTIALLY MET, MISSING, AMBIGUOUS, NOT VERIFIABLE
    supporting_evidence: Optional[str] = None
    source_document_name: Optional[str] = None
    page_number: Optional[int] = None
    bbox: Optional[List[float]] = None
    explanation: str
    confidence: float
    created_at: datetime

    class Config:
        from_attributes = True


class RequirementAssessmentCreate(BaseModel):
    target_document_id: str
    requirement_set_id: Optional[str] = None
    manual_requirements: Optional[List[str]] = None
    inspection_id: Optional[str] = None


class RequirementAssessmentResponse(BaseModel):
    id: str
    requirement_set_id: str
    target_document_id: str
    inspection_id: Optional[str] = None
    status: str
    summary: Optional[Dict[str, int]] = None
    results: List[RequirementResultResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True

