from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "RAVENX AI"
    TAGLINE: str = "Intelligence That Sees What Others Miss."
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Server Network
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Database & Supabase
    DATABASE_URL: str = "sqlite:///./ravenx_dev.db"
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_STORAGE_BUCKET: str = "documents"

    # Upload Constraints & Storage
    LOCAL_UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_BYTES: int = 25 * 1024 * 1024  # 25MB
    ALLOWED_FILE_EXTENSIONS: List[str] = ["pdf", "docx", "pptx"]
    MAX_EXTRACTION_TIMEOUT_SECONDS: int = 60

    # AI Providers
    DEFAULT_AI_PROVIDER: str = "deepseek"
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_API_BASE: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-pro"

    LANGUAGETOOL_ENABLED: bool = False
    LANGUAGETOOL_API_URL: str = "https://api.languagetool.org/v2"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()

