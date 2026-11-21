from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    documents,
    inspections,
    settings,
    extraction,
    requirements,
    comparisons,
    audit,
    correction
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(extraction.router, tags=["Extraction"])
api_router.include_router(inspections.router, prefix="/inspections", tags=["Inspections"])
api_router.include_router(correction.router, tags=["Correction"])
api_router.include_router(requirements.router, prefix="/requirements", tags=["Requirements"])
api_router.include_router(comparisons.router, prefix="/comparisons", tags=["Comparisons"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit"])
api_router.include_router(settings.router, prefix="/settings", tags=["Settings"])
