from datetime import datetime
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="healthy", description="Application service status")
    project: str = Field(default="RAVENX AI")
    version: str = Field(default="0.1.0")
    environment: str = Field(default="development")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: dict = Field(
        default_factory=lambda: {
            "database": "connected",
            "storage": "ready",
            "ai_providers": "configured"
        }
    )

