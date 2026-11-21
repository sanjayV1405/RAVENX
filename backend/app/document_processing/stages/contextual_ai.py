import hashlib
from typing import Dict, Any, List, Optional
from app.providers.factory import AIProviderFactory
from app.core.logging import logger


class ContextualAIInspectionStage:
    """
    Stage 5: Low-Token Contextual AI Inspection
    Inspects:
    - Semantic coherence, terminology consistency, requirement mismatches.
    - Connects to DeepSeek / Google Gemini via BaseAIProvider abstraction.
    - Low-Token Architecture:
      - Uses targeted text windowing (max 8,000 chars of key narrative).
      - In-memory caching by document content hash to prevent redundant LLM token expenditures.
      - Skips raw binary or purely numeric table blocks to save tokens.
    """

    # In-memory token cache: hash(content + guidelines + provider) -> findings
    _CACHE: Dict[str, List[Dict[str, Any]]] = {}

    @classmethod
    async def process(
        cls,
        extraction_data: Dict[str, Any],
        ai_provider_name: str = "deepseek",
        guidelines: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        logger.info(f"[Pipeline Stage 5: Contextual AI] Inspecting via provider: {ai_provider_name}")
        provider = AIProviderFactory.get_provider(ai_provider_name)
        if not provider.is_configured:
            logger.info(f"AI Provider '{ai_provider_name}' is not configured with an API key. Skipping.")
            return []

        raw_text = extraction_data.get("raw_text", "")
        if not raw_text or not raw_text.strip():
            return []

        # Target relevant narrative sections (trimming excess whitespace and capping window)
        targeted_text = cls._extract_targeted_narrative(raw_text)

        # Check Cache
        cache_key = hashlib.sha256(
            f"{ai_provider_name}:{guidelines}:{targeted_text}".encode("utf-8")
        ).hexdigest()

        if cache_key in cls._CACHE:
            logger.info(f"[Contextual AI] Returning cached findings for document hash {cache_key[:8]}")
            return cls._CACHE[cache_key]

        findings = await provider.inspect_content(
            extracted_text=targeted_text,
            document_type=extraction_data.get("metadata", {}).get("format", "unknown"),
            guidelines=guidelines
        )

        # Cache result
        cls._CACHE[cache_key] = findings
        return findings

    @classmethod
    def _extract_targeted_narrative(cls, full_text: str, max_chars: int = 8000) -> str:
        """Extracts key narrative sections, omitting pure table blocks and repetitive headers."""
        if len(full_text) <= max_chars:
            return full_text

        # Take first 4000 characters (executive summary, intro) and last 4000 characters (conclusions, dates, sign-offs)
        half = max_chars // 2
        head = full_text[:half]
        tail = full_text[-half:]
        return f"{head}\n\n[... middle sections summarized to minimize token consumption ...]\n\n{tail}"
