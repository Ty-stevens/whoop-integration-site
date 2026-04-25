from dataclasses import dataclass
from typing import Any, Literal

AiProviderName = Literal["disabled", "openai_compatible", "openclaw"]
AiResponseFormat = dict[str, Any]


@dataclass(frozen=True)
class AiProviderResult:
    text: str


class AiProviderError(RuntimeError):
    pass


AiContext = dict[str, Any]
