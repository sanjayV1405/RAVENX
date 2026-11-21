import json
import httpx
from typing import Dict, Any, List, Optional
from app.providers.base import BaseAIProvider
from app.core.config import settings
from app.core.logging import logger


class DeepSeekProvider(BaseAIProvider):
    """
    Adapter for DeepSeek API for deep contextual reasoning, structural analysis,
    and consistency checking across complex business and technical documents.
    Enforces strict anti-hallucination validation on original text excerpts.
    """

    def __init__(self):
        super().__init__(
            provider_name="deepseek",
            model_name=settings.DEEPSEEK_MODEL or "deepseek-chat",
            api_key=settings.DEEPSEEK_API_KEY
        )
        self.api_base = settings.DEEPSEEK_API_BASE or "https://api.deepseek.com/v1"

    async def inspect_content(
        self,
        extracted_text: str,
        document_type: str,
        guidelines: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        if not self.is_configured:
            logger.info("DeepSeek API key is not configured. Falling back to deterministic rules.")
            return []

        if not extracted_text or not extracted_text.strip():
            return []

        prompt = (
            "You are RAVENX AI, an elite document intelligence engine. "
            "Inspect the following extracted document text for subtle errors that ordinary checkers miss:\n"
            "- Factual or internal contradictions.\n"
            "- Missing clauses, ambiguous phrasing, or requirement discrepancies.\n"
            "- Inconsistent terminology or broken logical continuity.\n\n"
            f"Document Type: {document_type}\n"
            f"User Guidelines: {guidelines or 'Standard professional document quality'}\n\n"
            "Respond ONLY with a valid JSON array of objects with the following schema:\n"
            "[\n"
            "  {\n"
            '    "category": "contextual_ai",\n'
            '    "title": "Short title",\n'
            '    "page_number": 1,\n'
            '    "original_content": "Exact substring from the text that has the issue",\n'
            '    "suggested_correction": "Recommended correction",\n'
            '    "explanation": "Clear reason for the correction",\n'
            '    "severity": "critical" | "high" | "medium" | "low" | "info",\n'
            '    "confidence": 0.85\n'
            "  }\n"
            "]\n"
            "CRITICAL: The 'original_content' MUST be an exact verbatim substring present in the document. Do not invent or summarize."
        )

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{self.api_base.rstrip('/')}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model_name,
                        "messages": [
                            {"role": "system", "content": prompt},
                            {"role": "user", "content": extracted_text[:12000]}  # Context window guard
                        ],
                        "temperature": 0.1,
                        "response_format": {"type": "json_object"}
                    }
                )

                if response.status_code != 200:
                    logger.warning(f"DeepSeek API call returned status {response.status_code}: {response.text}")
                    return []

                data = response.json()
                content = data["choices"][0]["message"]["content"]
                parsed = json.loads(content)
                if isinstance(parsed, dict) and "findings" in parsed:
                    raw_findings = parsed["findings"]
                elif isinstance(parsed, list):
                    raw_findings = parsed
                else:
                    raw_findings = []

                # Grounding & anti-hallucination check
                grounded_findings = []
                for item in raw_findings:
                    orig = item.get("original_content", "").strip()
                    # Ensure original excerpt actually exists in the source text
                    if orig and orig.lower() in extracted_text.lower():
                        grounded_findings.append({
                            "category": "contextual_ai",
                            "title": item.get("title", "AI Contextual Insight"),
                            "page_number": item.get("page_number", 1),
                            "original_content": orig,
                            "suggested_correction": item.get("suggested_correction", ""),
                            "explanation": item.get("explanation", ""),
                            "severity": item.get("severity", "medium").lower(),
                            "confidence": min(1.0, max(0.1, float(item.get("confidence", 0.85)))),
                            "evidence_source": f"deepseek_{self.model_name}",
                            "detection_method": "llm_inference"
                        })
                    else:
                        logger.warning(f"Filtered out ungrounded AI finding with original_content: '{orig}'")

                return grounded_findings

        except Exception as e:
            logger.warning(f"DeepSeek contextual inspection exception: {e}")
            return []
