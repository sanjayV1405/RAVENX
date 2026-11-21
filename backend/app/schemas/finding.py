from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field


class FindingBase(BaseModel):
    category: str = Field(..., description="Category: micro_typography, grammar, entity_consistency, visual_layout, structural, contextual_ai, requirement_mismatch")
    title: str = Field(..., description="Short descriptive title of the finding")
    finding_classification: Optional[str] = Field("A", description="Classification: A=source_defect, B=extraction_uncertainty, C=layout_visual, D=contextual_inconsistency")
    is_actionable: Optional[bool] = Field(True, description="Whether this finding is an actionable text replacement rather than an advisory-only layout note")
    page_number: Optional[int] = Field(1, description="Page or slide number where the issue was detected")
    original_content: str = Field(..., description="Exact original content or problematic excerpt")
    suggested_correction: str = Field(..., description="Recommended correction or modification")
    explanation: str = Field(..., description="Evidence-backed reasoning and context behind the suggestion")
    severity: str = Field(default="medium", description="Severity level: critical, high, medium, low, info")
    confidence: float = Field(default=0.9, ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    evidence_source: Optional[str] = Field("deterministic_rule", description="Subsystem or provider producing the evidence")
    bbox: Optional[List[float]] = Field(None, description="Bounding box [x0, y0, x1, y1] on page if available")
    char_offset_start: Optional[int] = Field(None, description="Character offset start in block or page")
    char_offset_end: Optional[int] = Field(None, description="Character offset end in block or page")
    detection_method: Optional[str] = Field("rule_based", description="Detection method: rule_based, geometry_analysis, entity_crosscheck, llm_inference")
    verification_status: Optional[str] = Field("DETECTED", description="Verification state: DETECTED, VERIFIED, NEEDS_REVIEW, REJECTED, CONFLICT")
    source_location: Optional[Any] = Field(None, description="Structured source location details")


class FindingCreate(FindingBase):
    inspection_id: str


class FindingStatusUpdate(BaseModel):
    user_status: str = Field(..., description="User review status: needs_review, accepted, rejected, ignored")


class FindingResponse(FindingBase):
    id: str
    inspection_id: str
    user_status: str = "needs_review"
    reviewed_at: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

