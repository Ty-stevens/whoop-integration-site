import httpx

from app.core.config import Settings
from app.services.ai.types import AiProviderError, AiProviderResult


class OpenAiCompatibleProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate(self, prompt: str) -> AiProviderResult:
        if not self.settings.ai_base_url or not self.settings.ai_model:
            raise AiProviderError("AI provider is not configured")

        headers = {"Content-Type": "application/json"}
        if self.settings.ai_api_key:
            headers["Authorization"] = f"Bearer {self.settings.ai_api_key}"

        payload = {
            "model": self.settings.ai_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.settings.ai_max_output_tokens,
        }
        try:
            response = httpx.post(
                self.settings.ai_base_url.rstrip("/") + "/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.settings.ai_timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            raise AiProviderError("AI provider request failed") from exc

        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AiProviderError("AI provider returned an unexpected response") from exc
        return AiProviderResult(text=text)
