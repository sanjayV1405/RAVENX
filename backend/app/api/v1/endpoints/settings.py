from fastapi import APIRouter
from app.core.config import settings
from app.schemas.settings import SystemSettingsResponse, AIProviderConfig
from app.providers.deepseek_provider import DeepSeekProvider
from app.providers.gemini_provider import GeminiProvider

router = APIRouter()


@router.get("", response_model=SystemSettingsResponse)
def get_settings():
    """Retrieves current operational settings, provider statuses, and constraints."""
    deepseek = DeepSeekProvider()
    gemini = GeminiProvider()

    providers = [
        AIProviderConfig(
            provider_name="DeepSeek Reasoning",
            is_active=settings.DEFAULT_AI_PROVIDER == "deepseek",
            is_configured=deepseek.is_configured,
            model_name=deepseek.model_name,
            api_base=deepseek.api_base,
        ),
        AIProviderConfig(
            provider_name="Google Gemini",
            is_active=settings.DEFAULT_AI_PROVIDER == "gemini",
            is_configured=gemini.is_configured,
            model_name=gemini.model_name,
            api_base="https://generativelanguage.googleapis.com",
        ),
    ]

    return SystemSettingsResponse(
        project_name=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        default_ai_provider=settings.DEFAULT_AI_PROVIDER,
        max_file_size_mb=settings.MAX_FILE_SIZE_BYTES / (1024 * 1024),
        allowed_extensions=settings.ALLOWED_FILE_EXTENSIONS,
        ai_providers=providers,
        storage_type="Supabase Storage" if settings.SUPABASE_KEY else "Local File Storage (Dev Fallback)"
    )

