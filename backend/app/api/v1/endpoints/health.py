from fastapi import APIRouter
from app.schemas.health import HealthResponse
from app.core.config import settings
from app.database.supabase import supabase_service

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
def get_health():
    """Health check endpoint to verify backend operational readiness."""
    return HealthResponse(
        status="healthy",
        project=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        services={
            "database": "sqlite_active" if "sqlite" in settings.DATABASE_URL else "postgresql_active",
            "storage": "supabase_connected" if supabase_service.is_configured else "local_fallback",
            "ai_providers": settings.DEFAULT_AI_PROVIDER
        }
    )

