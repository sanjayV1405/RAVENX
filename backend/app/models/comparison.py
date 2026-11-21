import uuid
from sqlalchemy import Column, String, Integer, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.session import Base
from app.models.base import TimeStampedModel


class DocumentComparison(Base, TimeStampedModel):
    """Represents a comparative audit between two documents."""
    __tablename__ = "document_comparisons"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    base_document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    target_document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="completed", nullable=False)  # pending, processing, completed, failed
    summary = Column(JSON, nullable=True)  # counts of added, removed, modified, formatting_only, inconsistent

    differences = relationship("ComparisonDifference", back_populates="comparison", cascade="all, delete-orphan")


class ComparisonDifference(Base, TimeStampedModel):
    """An individual identified discrepancy between base and target documents."""
    __tablename__ = "comparison_differences"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    comparison_id = Column(String(36), ForeignKey("document_comparisons.id", ondelete="CASCADE"), nullable=False)
    
    # Category: content, structural, formatting
    category = Column(String(50), nullable=False)
    # Diff Type: added, removed, modified, potentially_inconsistent, formatting_only
    diff_type = Column(String(50), nullable=False)
    
    title = Column(String(200), nullable=False)
    base_page = Column(Integer, nullable=True)
    target_page = Column(Integer, nullable=True)
    base_content = Column(Text, nullable=True)
    target_content = Column(Text, nullable=True)
    explanation = Column(Text, nullable=False)
    significance = Column(String(20), default="medium", nullable=False)  # high, medium, low

    comparison = relationship("DocumentComparison", back_populates="differences")

