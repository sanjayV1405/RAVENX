from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class AuditLogResponse(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    event_type: str
    actor: str
    summary: str
    details: Optional[Dict[str, Any]] = None
    event_timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True

