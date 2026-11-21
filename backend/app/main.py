import os
import time
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import RavenXException
from app.api.v1.api import api_router
from app.database.session import engine, Base
import app.models  # Ensures all models are registered on Base.metadata

# Initialize tables in dev mode
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database schemas verified and initialized.")
    # Safe column upgrade for Phase 3 finding fields
    if settings.DATABASE_URL.startswith("sqlite"):
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(findings)"))
            existing_cols = {row[1] for row in result.fetchall()}
            new_cols = [
                ("evidence_source", "VARCHAR(100) DEFAULT 'deterministic_rule'"),
                ("bbox", "JSON"),
                ("char_offset_start", "INTEGER"),
                ("char_offset_end", "INTEGER"),
                ("detection_method", "VARCHAR(50) DEFAULT 'rule_based'"),
                ("finding_classification", "VARCHAR(10) DEFAULT 'A'")
            ]
            for col_name, col_def in new_cols:
                if col_name not in existing_cols:
                    conn.execute(text(f"ALTER TABLE findings ADD COLUMN {col_name} {col_def}"))
                    logger.info(f"Added column '{col_name}' to findings table.")
            conn.commit()
except Exception as e:
    logger.warning(f"Could not automatically initialize tables: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="RAVENX AI: Intelligence That Sees What Others Miss. Advanced Document Quality Inspection Platform.",
    version=settings.VERSION,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Also expose under /api/v1 prefix for backwards compatibility
@app.get("/api/v1/docs", include_in_schema=False)
def get_v1_docs():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")

# CORS Configuration for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Centralized Exception Handling
@app.exception_handler(RavenXException)
async def ravenx_exception_handler(request: Request, exc: RavenXException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error_type": exc.__class__.__name__},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled system error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal system error occurred. Please contact the administrator."},
    )


# Root health check endpoint
@app.get("/", tags=["Health"])
def root_health():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "tagline": settings.TAGLINE,
        "version": settings.VERSION,
        "api_docs": f"{settings.API_V1_STR}/docs"
    }


# Include V1 API Router
app.include_router(api_router, prefix=settings.API_V1_STR)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
