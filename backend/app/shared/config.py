"""Typed, cached application configuration."""

from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed settings. Unknown variables are ignored intentionally."""

    model_config = SettingsConfigDict(env_prefix="PARKSHIELD_", extra="ignore")

    environment: Literal["local", "test", "staging", "production"] = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    api_v1_prefix: str = "/api/v1"
    jwt_secret: str = "local-development-secret-change-before-production"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 30
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    email_from: str = "no-reply@parkshield.ai"
    mobile_link_scheme: str = "parkshield"
    database_url: str = "postgresql+asyncpg://parkshield:change-me@localhost:5432/parkshield"
    push_provider_url: str | None = None
    push_provider_token: str | None = None
    tow_provider_url: str | None = None
    tow_provider_token: str | None = None
    media_bucket: str | None = None
    media_retention_days: int = Field(default=30, ge=1, le=30)

    @model_validator(mode="after")
    def validate_deployed_environment(self) -> Self:
        """Reject development defaults and disabled critical providers before startup."""
        if self.environment not in {"staging", "production"}:
            return self

        errors: list[str] = []
        if len(self.jwt_secret) < 32 or "change" in self.jwt_secret.casefold():
            errors.append("jwt_secret must be a non-default secret of at least 32 characters")
        database_url = self.database_url.casefold()
        if (
            "change-me" in database_url
            or "localhost" in database_url
            or "ssl=require" not in database_url
        ):
            errors.append("database_url must reference the deployed database and require TLS")
        if not all((self.smtp_host, self.smtp_username, self.smtp_password)):
            errors.append("SMTP credentials are required")
        push_url = self.push_provider_url
        if not all((push_url, self.push_provider_token)):
            errors.append("push provider credentials are required")
        elif push_url is not None and not push_url.startswith("https://"):
            errors.append("push provider URL must use HTTPS")
        tow_url = self.tow_provider_url
        if not all((tow_url, self.tow_provider_token)):
            errors.append("tow lookup provider credentials are required")
        elif tow_url is not None and not tow_url.startswith("https://"):
            errors.append("tow lookup provider URL must use HTTPS")
        if not self.media_bucket or not self.media_bucket.strip():
            errors.append("media_bucket is required for governed community evidence")
        if errors:
            raise ValueError("; ".join(errors))
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
