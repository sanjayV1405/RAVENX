from typing import Optional, List
from pydantic import BaseModel, Field


class AIProviderConfig(BaseModel):
    provider_name: str
    is_active: bool
    is_configured: bool
    model_name: str
    api_base: Optional[str] = None


class SystemSettingsResponse(BaseModel):
    project_name: str
    version: str
    environment: str
    default_ai_provider: str
    max_file_size_mb: float
    allowed_extensions: List[str]
    ai_providers: List[AIProviderConfig]
    storage_type: str

