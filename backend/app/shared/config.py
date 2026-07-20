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
    privacy_policy_version: str = Field(
        default="2026-07-17", min_length=1, max_length=32, pattern=r"^[A-Za-z0-9._-]+$"
    )
    municipal_imports_enabled: bool = False
    municipal_max_upload_bytes: int = Field(
        default=5 * 1024 * 1024, ge=1024, le=10 * 1024 * 1024
    )
    billing_enabled: bool = False
    billing_subject_secret: str = "local-billing-subject-secret-change-before-production"
    billing_gateway_url: str | None = None
    billing_gateway_token: str | None = None
    apple_premium_product_id: str | None = None
    google_premium_product_id: str | None = None
    observability_provider: Literal["disabled", "memory", "opentelemetry"] = "memory"
    observability_export_enabled: bool = False
    observability_otlp_endpoint: str | None = None
    observability_service_name: str = Field(
        default="parkshield-api", min_length=1, max_length=64, pattern=r"^[A-Za-z0-9._-]+$"
    )
    product_analytics_enabled: bool = False
    product_analytics_provider: Literal["disabled", "memory", "external"] = "disabled"
    product_analytics_subject_secret: str = (
        "local-analytics-subject-secret-change-before-production"
    )
    product_analytics_retention_days: int = Field(default=30, ge=1, le=90)

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
        if (
            len(self.billing_subject_secret) < 32
            or "change" in self.billing_subject_secret.casefold()
        ):
            errors.append(
                "billing_subject_secret must be a non-default secret of at least 32 characters"
            )
        if self.billing_enabled:
            billing_url = self.billing_gateway_url
            if not all((billing_url, self.billing_gateway_token)):
                errors.append("billing verification gateway credentials are required")
            elif billing_url is not None and not billing_url.startswith("https://"):
                errors.append("billing verification gateway URL must use HTTPS")
            if not any(
                (self.apple_premium_product_id, self.google_premium_product_id)
            ):
                errors.append("at least one approved store product ID is required")
        if self.observability_export_enabled:
            if self.observability_provider != "opentelemetry":
                errors.append(
                    "observability export requires the opentelemetry provider"
                )
            endpoint = self.observability_otlp_endpoint
            if endpoint is None or not endpoint.startswith("https://"):
                errors.append("observability OTLP endpoint must use HTTPS")
        if self.product_analytics_enabled:
            if self.product_analytics_provider != "external":
                errors.append(
                    "product analytics requires an external provider in deployed environments"
                )
            if (
                len(self.product_analytics_subject_secret) < 32
                or "change" in self.product_analytics_subject_secret.casefold()
            ):
                errors.append(
                    "product_analytics_subject_secret must be a non-default secret "
                    "of at least 32 characters"
                )
        if errors:
            raise ValueError("; ".join(errors))
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
