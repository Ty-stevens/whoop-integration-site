from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(ROOT_DIR / ".env.local", ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: Literal["development", "test", "production"] = "development"
    app_name: str = "EnduraSync"
    app_version: str = "0.1.0"
    app_base_url: str = "http://localhost:8000"
    frontend_dev_url: str = "http://localhost:5173"
    database_url: str = "sqlite:///./data/endurasync.db"
    app_encryption_key: str = "replace-me"

    whoop_client_id: str = "replace-me"
    whoop_client_secret: str = "replace-me"
    whoop_redirect_uri: str = "http://localhost:8000/api/v1/integrations/whoop/callback"
    whoop_authorization_url: str = "https://api.prod.whoop.com/oauth/oauth2/auth"
    whoop_token_url: str = "https://api.prod.whoop.com/oauth/oauth2/token"
    whoop_api_base_url: str = "https://api.prod.whoop.com/developer"

    cors_origins_raw: str = Field("http://localhost:5173", alias="CORS_ORIGINS")
    auto_sync_enabled: bool = False
    auto_sync_frequency: Literal["daily", "twice_daily"] = "daily"

    ai_enabled: bool = False
    ai_provider: Literal["disabled", "openai_compatible", "openclaw"] = "disabled"
    ai_base_url: str = ""
    ai_model: str = ""
    ai_api_key: str = ""
    ai_timeout_seconds: int = 30
    ai_max_input_tokens: int = 12000
    ai_max_output_tokens: int = 1200

    @field_validator("ai_timeout_seconds")
    @classmethod
    def validate_ai_timeout(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("AI_TIMEOUT_SECONDS must be positive")
        return value

    @field_validator("ai_max_input_tokens", "ai_max_output_tokens")
    @classmethod
    def validate_ai_token_limits(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("AI token limits must be positive")
        return value

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]

    @property
    def whoop_credentials_configured(self) -> bool:
        return not _is_placeholder_secret(self.whoop_client_id) and not _is_placeholder_secret(
            self.whoop_client_secret
        )

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.app_env == "production":
            placeholders = {
                "APP_ENCRYPTION_KEY": self.app_encryption_key,
                "WHOOP_CLIENT_ID": self.whoop_client_id,
                "WHOOP_CLIENT_SECRET": self.whoop_client_secret,
            }
            missing = [
                name for name, value in placeholders.items() if _is_placeholder_secret(value)
            ]
            if missing:
                names = ", ".join(missing)
                raise ValueError(
                    f"Production configuration requires non-placeholder secrets: {names}"
                )
        if self.ai_enabled and self.ai_provider == "disabled":
            raise ValueError("AI_PROVIDER cannot be disabled when AI_ENABLED=true")
        return self


def _is_placeholder_secret(value: str) -> bool:
    normalized = value.strip().lower()
    return (
        not normalized
        or normalized == "replace-me"
        or normalized.startswith("replace-with")
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
