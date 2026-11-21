from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.audit_log import AuditLogResponse
from app.services.audit_service import AuditService

router = APIRouter()


@router.get("/history", response_model=List[AuditLogResponse])
def get_audit_history(
    entity_type: Optional[str] = Query(None, description="Filter by entity type (finding, inspection, document, comparison, requirement)"),
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Returns the immutable chronological audit trail of all inspection, review, and comparison actions.
    """
    return AuditService.get_history(db=db, entity_type=entity_type, entity_id=entity_id, limit=limit)

