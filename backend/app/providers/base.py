from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class BaseAIProvider(ABC):
    """
    Abstract base class for all AI reasoning and inspection providers in RAVENX AI.
    Ensures modular, interchangeable LLM integrations without modifying core logic.
    """

    def __init__(self, provider_name: str, model_name: str, api_key: Optional[str] = None):
        self.provider_name = provider_name
        self.model_name = model_name
        self.api_key = api_key

    @property
    def is_configured(self) -> bool:
        """Determines whether the provider has the necessary credentials configured."""
        return bool(self.api_key and len(self.api_key.strip()) > 0)

    @abstractmethod
    async def inspect_content(
        self,
        extracted_text: str,
        document_type: str,
        guidelines: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes contextual reasoning inspection over document contents.
        Must return structured finding dictionaries conforming to the finding schema.
        """
        pass

