from typing import Dict, Type
from app.providers.base import BaseAIProvider
from app.providers.deepseek_provider import DeepSeekProvider
from app.providers.gemini_provider import GeminiProvider
from app.core.config import settings
from app.core.logging import logger


class AIProviderFactory:
    """Factory to retrieve configured AI providers by name."""

    _registry: Dict[str, Type[BaseAIProvider]] = {
        "deepseek": DeepSeekProvider,
        "gemini": GeminiProvider,
    }

    @classmethod
    def get_provider(cls, name: str = None) -> BaseAIProvider:
        provider_name = (name or settings.DEFAULT_AI_PROVIDER).lower()
        provider_class = cls._registry.get(provider_name)
        if not provider_class:
            logger.warning(f"Unknown provider '{provider_name}', falling back to 'deepseek'")
            provider_class = DeepSeekProvider
        return provider_class()

    @classmethod
    def list_available_providers(cls):
        return list(cls._registry.keys())

