import json
import httpx
from typing import Dict, Any, List, Optional
from app.providers.base import BaseAIProvider
from app.core.config import settings
from app.core.logging import logger


class GeminiProvider(BaseAIProvider):
    """
    Adapter for Google Gemini API for independent secondary cross-validation,
    multimodal layout comprehension, and semantic anomaly detection.
    Enforces strict anti-hallucination validation on original text excerpts.
    """

    def __init__(self):
        super().__init__(
            provider_name="gemini",
            model_name=settings.GEMINI_MODEL or "gemini-1.5-pro",
            api_key=settings.GEMINI_API_KEY
        )

    async def inspect_content(
        self,
        extracted_text: str,
        document_type: str,
        guidelines: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        if not self.is_configured:
            logger.info("Gemini API key is not configured. Falling back to deterministic rules.")
            return []

        if not extracted_text or not extracted_text.strip():
            return []

        prompt = (
            "You are RAVENX AI document intelligence engine. "
            "Inspect the following extracted text for subtle inconsistencies and quality defects.\n"
            f"Document Type: {document_type}\n"
            f"Guidelines: {guidelines or 'Professional publication quality'}\n\n"
            "Return a JSON array of findings with keys: category, title, page_number, original_content, "
            "suggested_correction, explanation, severity ('critical'|'high'|'medium'|'low'|'info'), confidence (0.0 to 1.0).\n"
            "CRITICAL: 'original_content' must be an exact verbatim substring from the provided text."
        )

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": f"{prompt}\n\nDOCUMENT TEXT:\n{extracted_text[:12000]}"}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,
                    "responseMimeType": "application/json"
                }
            }

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code != 200:
                    logger.warning(f"Gemini API returned status {response.status_code}: {response.text}")
                    return []

                data = response.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(raw_text)
                if isinstance(parsed, dict) and "findings" in parsed:
                    raw_findings = parsed["findings"]
                elif isinstance(parsed, list):
                    raw_findings = parsed
                else:
                    raw_findings = []

                grounded_findings = []
                for item in raw_findings:
                    orig = item.get("original_content", "").strip()
                    if orig and orig.lower() in extracted_text.lower():
                        grounded_findings.append({
                            "category": "contextual_ai",
                            "title": item.get("title", "Gemini Contextual Finding"),
                            "page_number": item.get("page_number", 1),
                            "original_content": orig,
                            "suggested_correction": item.get("suggested_correction", ""),
                            "explanation": item.get("explanation", ""),
                            "severity": item.get("severity", "medium").lower(),
                            "confidence": min(1.0, max(0.1, float(item.get("confidence", 0.85)))),
                            "evidence_source": f"gemini_{self.model_name}",
                            "detection_method": "llm_inference"
                        })
                    else:
                        logger.warning(f"Filtered out ungrounded Gemini finding with original_content: '{orig}'")

                return grounded_findings

        except Exception as e:
            logger.warning(f"Gemini contextual inspection exception: {e}")
            return []
