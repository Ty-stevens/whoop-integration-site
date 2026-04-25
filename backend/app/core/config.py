import os
from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

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
    api_auth_token: str = ""
    trusted_hosts_raw: str = Field("localhost,127.0.0.1,testserver", alias="TRUSTED_HOSTS")
    api_docs_enabled: bool = Field(True, alias="API_DOCS_ENABLED")

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
    openai_api_key: str = ""
    openai_model: str = ""
    openai_base_url: str = "https://api.openai.com/v1"

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

    @field_validator("app_base_url", "frontend_dev_url", "whoop_redirect_uri")
    @classmethod
    def validate_public_urls(cls, value: str) -> str:
        return _validate_http_url(value, setting_name="public URL")

    @field_validator("whoop_authorization_url", "whoop_token_url", "whoop_api_base_url")
    @classmethod
    def validate_provider_urls(cls, value: str) -> str:
        return _validate_http_url(value, setting_name="WHOOP URL")

    @field_validator("ai_base_url", "openai_base_url")
    @classmethod
    def validate_ai_base_url(cls, value: str) -> str:
        if not value:
            return value
        return _validate_http_url(value, setting_name="AI_BASE_URL")

    @field_validator("cors_origins_raw")
    @classmethod
    def validate_cors_origins(cls, value: str) -> str:
        origins = [origin.strip() for origin in value.split(",") if origin.strip()]
        if not origins:
            raise ValueError("CORS_ORIGINS must include at least one origin")
        for origin in origins:
            if origin == "*":
                raise ValueError("CORS_ORIGINS cannot include '*' when credentials are enabled")
            _validate_http_url(origin, setting_name="CORS_ORIGINS origin")
        return value

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]

    @property
    def trusted_hosts(self) -> list[str]:
        hosts = [host.strip() for host in self.trusted_hosts_raw.split(",") if host.strip()]
        hosts = hosts or ["localhost", "127.0.0.1", "testserver"]
        for url in (self.app_base_url, self.frontend_dev_url):
            _append_url_hostname(hosts, url)
        vercel_url = os.getenv("VERCEL_URL")
        if vercel_url:
            _append_url_hostname(hosts, f"https://{vercel_url}")
        return hosts

    @property
    def api_auth_enabled(self) -> bool:
        return not _is_placeholder_secret(self.api_auth_token)

    @property
    def database_is_ephemeral(self) -> bool:
        return bool(os.getenv("VERCEL")) and self.database_url.startswith("sqlite:")

    @property
    def database_storage_status(self) -> Literal["durable", "ephemeral"]:
        return "ephemeral" if self.database_is_ephemeral else "durable"

    @property
    def database_storage_message(self) -> str:
        if self.database_is_ephemeral:
            return (
                "Vercel deployments need a durable DATABASE_URL such as Neon Postgres. "
                "SQLite is stored in ephemeral function storage and cannot retain WHOOP "
                "OAuth tokens or synced health data."
            )
        return "Database storage is durable for this runtime."

    @property
    def whoop_credentials_configured(self) -> bool:
        return not _is_placeholder_secret(self.whoop_client_id) and not _is_placeholder_secret(
            self.whoop_client_secret
        )

    @property
    def effective_ai_base_url(self) -> str:
        if self.ai_base_url:
            return self.ai_base_url
        if self.ai_provider == "openai_compatible":
            return self.openai_base_url
        if self.openai_api_key or self.openai_model:
            return self.openai_base_url
        return ""

    @property
    def effective_ai_model(self) -> str:
        return self.ai_model or self.openai_model

    @property
    def effective_ai_api_key(self) -> str:
        return self.ai_api_key or self.openai_api_key

    @property
    def ai_setup_error(self) -> str | None:
        if not self.ai_enabled:
            return None
        if self.ai_provider == "disabled":
            return "Set AI_PROVIDER=openai_compatible before using AI features."
        if not self.effective_ai_base_url:
            return "Set AI_BASE_URL or OPENAI_BASE_URL before using AI features."
        if not self.effective_ai_model:
            return "Set AI_MODEL or OPENAI_MODEL before using AI features."
        if "api.openai.com" in self.effective_ai_base_url and not self.effective_ai_api_key:
            return "Set AI_API_KEY or OPENAI_API_KEY before using OpenAI features."
        return None

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.app_env == "production":
            if not all(_is_https_url(origin) for origin in self.cors_origins):
                raise ValueError("Production CORS_ORIGINS must use HTTPS origins")
            if not _is_https_or_local(self.app_base_url):
                raise ValueError("APP_BASE_URL must be HTTPS in production")
            if not _is_https_or_local(self.whoop_redirect_uri):
                raise ValueError("WHOOP_REDIRECT_URI must be HTTPS in production")
            if any(host == "*" for host in self.trusted_hosts):
                raise ValueError("TRUSTED_HOSTS cannot include '*' in production")
        return self


def _is_placeholder_secret(value: str) -> bool:
    normalized = value.strip().lower()
    return (
        not normalized
        or normalized == "replace-me"
        or normalized.startswith("replace-with")
        or normalized in {"changeme", "your-secret-here", "set-me"}
    )


def _validate_http_url(value: str, *, setting_name: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{setting_name} must be a valid http(s) URL")
    return value


def _is_https_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "https"


def _is_https_or_local(value: str) -> bool:
    parsed = urlparse(value)
    if parsed.scheme == "https":
        return True
    hostname = parsed.hostname or ""
    return hostname in {"localhost", "127.0.0.1"}


def _append_url_hostname(hosts: list[str], value: str) -> None:
    parsed = urlparse(value)
    hostname = parsed.hostname
    if hostname and hostname not in hosts:
        hosts.append(hostname)


@lru_cache
def get_settings() -> Settings:
    return Settings()
