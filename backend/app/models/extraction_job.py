import uuid
import datetime
from sqlalchemy import Column, String, Integer, Text, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database.session import Base


class ExtractionJob(Base):
    __tablename__ = "extraction_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(30), default="queued", nullable=False)  # queued / processing / completed / failed
    extractor_type = Column(String(30), nullable=False)  # pdf / docx / pptx / ocr
    page_count = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    extraction_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    document = relationship("Document", back_populates="extraction_jobs")
    pages = relationship(
        "ExtractedPage",
        back_populates="extraction_job",
        cascade="all, delete-orphan",
        order_by="ExtractedPage.page_number"
    )
