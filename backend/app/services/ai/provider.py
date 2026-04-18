from abc import ABC, abstractmethod

from app.core.config import Settings
from app.services.ai.providers.disabled import DisabledAiProvider
from app.services.ai.providers.openai_compatible import OpenAiCompatibleProvider
from app.services.ai.types import AiProviderResult


class AiProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> AiProviderResult:
        raise NotImplementedError


def provider_from_settings(settings: Settings) -> AiProvider:
    if not settings.ai_enabled or settings.ai_provider == "disabled":
        return DisabledAiProvider()
    if settings.ai_provider in {"openai_compatible", "openclaw"}:
        return OpenAiCompatibleProvider(settings)
    return DisabledAiProvider()
