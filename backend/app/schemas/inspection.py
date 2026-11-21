from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.finding import FindingResponse


class InspectionCreate(BaseModel):
    document_id: str = Field(..., description="ID of the document to inspect")
    ai_provider: Optional[str] = Field("deepseek", description="AI provider to use (deepseek, gemini)")
    user_guidelines: Optional[str] = Field(None, description="Optional custom guidelines/requirements to validate against")


class InspectionResponse(BaseModel):
    id: str
    document_id: str
    status: str
    current_stage: Optional[str] = None
    progress_percentage: int
    ai_provider: str
    summary: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    findings: List[FindingResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

