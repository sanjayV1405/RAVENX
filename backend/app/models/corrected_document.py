import uuid
from sqlalchemy import Column, String, Integer, BigInteger, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.session import Base
from app.models.base import TimeStampedModel


class CorrectedDocument(Base, TimeStampedModel):
    __tablename__ = "corrected_documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    inspection_id = Column(String(36), ForeignKey("inspections.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    corrected_filename = Column(String(255), nullable=False)
    file_extension = Column(String(10), nullable=False)
    file_size_bytes = Column(BigInteger, default=0, nullable=False)
    storage_path = Column(String(500), nullable=False)
    checksum = Column(String(64), nullable=True)  # SHA-256 of the generated corrected file
    applied_findings_count = Column(Integer, default=0, nullable=False)
    correction_summary = Column(JSON, nullable=True)  # Detailed list/metrics of applied changes

    inspection = relationship("Inspection")
    document = relationship("Document")
