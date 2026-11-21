import uuid
from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.session import Base
from app.models.base import TimeStampedModel


class RequirementSet(Base, TimeStampedModel):
    """A collection of business, regulatory, or technical requirements."""
    __tablename__ = "requirement_sets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    source_type = Column(String(50), default="manual", nullable=False)  # manual, checklist, reference_doc
    reference_document_id = Column(String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)

    items = relationship("RequirementItem", back_populates="requirement_set", cascade="all, delete-orphan")
    assessments = relationship("RequirementAssessment", back_populates="requirement_set", cascade="all, delete-orphan")


class RequirementItem(Base, TimeStampedModel):
    """An individual clause, requirement, or verification rule."""
    __tablename__ = "requirement_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    requirement_set_id = Column(String(36), ForeignKey("requirement_sets.id", ondelete="CASCADE"), nullable=False)
    item_text = Column(Text, nullable=False)
    category = Column(String(100), default="general", nullable=False)
    importance = Column(String(50), default="mandatory", nullable=False)  # mandatory, recommended, optional

    requirement_set = relationship("RequirementSet", back_populates="items")


class RequirementAssessment(Base, TimeStampedModel):
    """An assessment run evaluating a document against a RequirementSet."""
    __tablename__ = "requirement_assessments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    requirement_set_id = Column(String(36), ForeignKey("requirement_sets.id", ondelete="CASCADE"), nullable=False)
    target_document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    inspection_id = Column(String(36), ForeignKey("inspections.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), default="completed", nullable=False)  # pending, completed, failed
    summary = Column(JSON, nullable=True)  # counts of MET, PARTIALLY_MET, MISSING, AMBIGUOUS, NOT_VERIFIABLE

    requirement_set = relationship("RequirementSet", back_populates="assessments")
    results = relationship("RequirementResult", back_populates="assessment", cascade="all, delete-orphan")


class RequirementResult(Base, TimeStampedModel):
    """The result of evaluating a single requirement against the target document."""
    __tablename__ = "requirement_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id = Column(String(36), ForeignKey("requirement_assessments.id", ondelete="CASCADE"), nullable=False)
    requirement_item_id = Column(String(36), nullable=True)
    requirement_text = Column(Text, nullable=False)
    
    # Status: MET, PARTIALLY MET, MISSING, AMBIGUOUS, NOT VERIFIABLE
    status = Column(String(50), nullable=False)
    supporting_evidence = Column(Text, nullable=True)
    source_document_name = Column(String(255), nullable=True)
    page_number = Column(Integer, nullable=True)
    bbox = Column(JSON, nullable=True)
    explanation = Column(Text, nullable=False)
    confidence = Column(Float, default=0.9, nullable=False)

    assessment = relationship("RequirementAssessment", back_populates="results")

