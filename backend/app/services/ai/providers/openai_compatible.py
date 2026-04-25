import logging

import httpx

from app.core.config import Settings
from app.services.ai.types import AiProviderError, AiProviderResult, AiResponseFormat

logger = logging.getLogger("endurasync.ai.provider")


class OpenAiCompatibleProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate(
        self,
        prompt: str,
        *,
        response_format: AiResponseFormat | None = None,
    ) -> AiProviderResult:
        setup_error = self.settings.ai_setup_error
        if setup_error:
            raise AiProviderError(setup_error)

        headers = {"Content-Type": "application/json"}
        if self.settings.effective_ai_api_key:
            headers["Authorization"] = f"Bearer {self.settings.effective_ai_api_key}"

        payload = {
            "model": self.settings.effective_ai_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.settings.ai_max_output_tokens,
        }
        if response_format is not None:
            payload["response_format"] = response_format
        try:
            logger.info(
                "ai.provider.request provider=%s model=%s response_format=%s",
                self.settings.ai_provider,
                self.settings.effective_ai_model,
                bool(response_format),
            )
            response = httpx.post(
                self.settings.effective_ai_base_url.rstrip("/") + "/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.settings.ai_timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            logger.warning("ai.provider.failed error_type=%s", exc.__class__.__name__)
            raise AiProviderError("AI provider request failed") from exc

        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            logger.warning("ai.provider.unexpected_response")
            raise AiProviderError("AI provider returned an unexpected response") from exc
        if not isinstance(text, str):
            logger.warning("ai.provider.non_text_response")
            raise AiProviderError("AI provider returned an unexpected response")
        logger.info("ai.provider.success characters=%s", len(text or ""))
        return AiProviderResult(text=text)
