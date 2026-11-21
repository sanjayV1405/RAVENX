from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.config import settings
from app.core.logging import logger

if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    """Initializes tables and ensures all necessary columns exist on SQLite."""
    try:
        import app.models  # ensure models are loaded
        Base.metadata.create_all(bind=engine)
        if settings.DATABASE_URL.startswith("sqlite"):
            with engine.connect() as conn:
                result = conn.execute(text("PRAGMA table_info(findings)"))
                existing_cols = {row[1] for row in result.fetchall()}
                new_cols = [
                    ("evidence_source", "VARCHAR(100) DEFAULT 'deterministic_rule'"),
                    ("bbox", "JSON"),
                    ("char_offset_start", "INTEGER"),
                    ("char_offset_end", "INTEGER"),
                    ("detection_method", "VARCHAR(50) DEFAULT 'rule_based'"),
                    ("finding_classification", "VARCHAR(10) DEFAULT 'A'"),
                    ("is_actionable", "BOOLEAN DEFAULT 1"),
                    ("verification_status", "VARCHAR(30) DEFAULT 'DETECTED'"),
                    ("source_location", "JSON")
                ]
                for col_name, col_def in new_cols:
                    if col_name not in existing_cols:
                        conn.execute(text(f"ALTER TABLE findings ADD COLUMN {col_name} {col_def}"))
                conn.commit()
    except Exception as e:
        logger.warning(f"Could not automatically initialize tables: {e}")


# Run initialization on import
init_db()


def get_db() -> Generator:
    """Dependency for obtaining database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
