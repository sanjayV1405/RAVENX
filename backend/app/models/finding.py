import uuid
from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from app.database.session import Base
from app.models.base import TimeStampedModel


class Finding(Base, TimeStampedModel):
    __tablename__ = "findings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    inspection_id = Column(String(36), ForeignKey("inspections.id", ondelete="CASCADE"), nullable=False)
    
    # Category: micro_typography, grammar, entity_consistency, visual_layout, structural, contextual_ai, requirement_mismatch
    category = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    
    # Classification: A=source_defect, B=extraction_uncertainty, C=layout_visual, D=contextual_inconsistency
    finding_classification = Column(String(10), default="A", nullable=False)
    is_actionable = Column(Boolean, default=True, nullable=False)  # False for layout/structure advisories
    
    # Evidence fields
    page_number = Column(Integer, nullable=True, default=1)
    original_content = Column(Text, nullable=False)
    suggested_correction = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)
    
    # Severity: critical, high, medium, low, info
    severity = Column(String(20), default="medium", nullable=False)
    confidence = Column(Float, default=0.9, nullable=False)  # 0.0 to 1.0
    
    # Evidence tracking & coordinates
    evidence_source = Column(String(100), default="deterministic_rule", nullable=False)
    bbox = Column(JSON, nullable=True)  # [x0, y0, x1, y1] coordinates
    char_offset_start = Column(Integer, nullable=True)
    char_offset_end = Column(Integer, nullable=True)
    detection_method = Column(String(50), default="rule_based", nullable=False)  # rule_based, geometry_analysis, entity_crosscheck, llm_inference
    
    # Verification & source mapping
    verification_status = Column(String(30), default="DETECTED", nullable=False)  # DETECTED, VERIFIED, NEEDS_REVIEW, REJECTED, CONFLICT
    source_location = Column(JSON, nullable=True)  # Structured SourceLocation dict (block_id, run_idx, cell, etc.)

    # User review state: never automatically applied (needs_review, accepted, rejected, ignored)
    user_status = Column(String(30), default="needs_review", nullable=False)
    reviewed_at = Column(String(50), nullable=True)
    
    inspection = relationship("Inspection", back_populates="findings")

