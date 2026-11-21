import datetime
from sqlalchemy import Column, DateTime, String
from app.database.session import Base


class TimeStampedModel:
    """Timestamp mixin for tracking creation and updates."""
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

