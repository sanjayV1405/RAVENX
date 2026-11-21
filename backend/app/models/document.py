import uuid
from sqlalchemy import Column, String, Integer, BigInteger
from sqlalchemy.orm import relationship
from app.database.session import Base
from app.models.base import TimeStampedModel


class Document(Base, TimeStampedModel):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    file_extension = Column(String(10), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=False)
    storage_path = Column(String(500), nullable=False)
    checksum = Column(String(64), nullable=True, index=True)  # SHA-256 for integrity & duplicate detection
    page_count = Column(Integer, nullable=True)
    status = Column(String(50), default="uploaded", nullable=False)  # uploaded, queued, processing, completed, failed

    inspections = relationship("Inspection", back_populates="document", cascade="all, delete-orphan")
    extraction_jobs = relationship("ExtractionJob", back_populates="document", cascade="all, delete-orphan")
