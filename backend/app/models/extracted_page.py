import uuid
import datetime
from sqlalchemy import Column, String, Integer, Float, Text, JSON, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.database.session import Base


class ExtractedPage(Base):
    __tablename__ = "extracted_pages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    extraction_job_id = Column(String(36), ForeignKey("extraction_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    raw_text = Column(Text, nullable=True)
    structured_data = Column(JSON, nullable=True)
    word_count = Column(Integer, default=0, nullable=False)
    has_tables = Column(Boolean, default=False, nullable=False)
    extraction_method = Column(String(20), default="native", nullable=False)  # native / ocr
    ocr_confidence = Column(Float, nullable=True)
    needs_ocr = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    extraction_job = relationship("ExtractionJob", back_populates="pages")
