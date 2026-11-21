import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.session import Base
from app.models.base import TimeStampedModel


class Inspection(Base, TimeStampedModel):
    __tablename__ = "inspections"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="pending", nullable=False)  # pending, processing, completed, failed
    current_stage = Column(String(100), nullable=True)
    progress_percentage = Column(Integer, default=0, nullable=False)
    ai_provider = Column(String(50), default="deepseek", nullable=False)
    summary = Column(JSON, nullable=True)  # { total_findings, high_severity, medium_severity, low_severity }
    error_message = Column(String(500), nullable=True)

    document = relationship("Document", back_populates="inspections")
    findings = relationship("Finding", back_populates="inspection", cascade="all, delete-orphan")

