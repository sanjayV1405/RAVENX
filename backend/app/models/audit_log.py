import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, JSON, DateTime
from app.database.session import Base
from app.models.base import TimeStampedModel


class AuditLog(Base, TimeStampedModel):
    """
    Immutable audit log recording all user decisions and inspection milestones.
    Never overwrites history; captures chronological trace of actions.
    """
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type = Column(String(50), nullable=False)  # finding, inspection, document, comparison, requirement, report
    entity_id = Column(String(36), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    # Event types:
    # finding_created, finding_accepted, finding_rejected, finding_ignored, finding_restored,
    # report_generated, comparison_performed, requirements_assessed, document_uploaded
    actor = Column(String(100), default="user", nullable=False)
    summary = Column(String(255), nullable=False)
    details = Column(JSON, nullable=True)
    event_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

