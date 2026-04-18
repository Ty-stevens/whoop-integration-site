from app.services.ai.types import AiProviderError, AiProviderResult


class DisabledAiProvider:
    def generate(self, prompt: str) -> AiProviderResult:
        raise AiProviderError("AI is disabled")
