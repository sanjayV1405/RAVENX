import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from app.core.logging import logger


class AuditService:
    """Service for maintaining the immutable audit trail of RAVENX AI actions."""

    @staticmethod
    def log_event(
        db: Session,
        entity_type: str,
        entity_id: str,
        event_type: str,
        summary: str,
        details: Optional[Dict[str, Any]] = None,
        actor: str = "user"
    ) -> AuditLog:
        entry = AuditLog(
            id=str(uuid.uuid4()),
            entity_type=entity_type,
            entity_id=entity_id,
            event_type=event_type,
            actor=actor,
            summary=summary,
            details=details or {},
            event_timestamp=datetime.utcnow()
        )
        try:
            db.add(entry)
            db.commit()
            db.refresh(entry)
            logger.info(f"[AuditLog] {event_type} on {entity_type}:{entity_id} - {summary}")
        except Exception as e:
            logger.error(f"Failed to record audit log: {e}")
            db.rollback()
        return entry

    @staticmethod
    def get_history(
        db: Session,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        query = db.query(AuditLog)
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        if entity_id:
            query = query.filter(AuditLog.entity_id == entity_id)
        return query.order_by(AuditLog.event_timestamp.desc()).limit(limit).all()

