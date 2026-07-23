import json
import logging

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import create_app
from app.shared.config import Settings


def deployed_settings(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "environment": "production",
        "jwt_secret": "a" * 64,
        "database_url": (
            "postgresql+asyncpg://app:secret@database.internal/parkshield?ssl=require"
        ),
        "smtp_host": "smtp.example.net",
        "smtp_username": "parkshield",
        "smtp_password": "smtp-secret",
        "push_provider_url": "https://push.example.net/messages",
        "push_provider_token": "push-secret",
        "tow_provider_url": "https://tow.example.net/lookup",
        "tow_provider_token": "tow-secret",
        "media_bucket": "parkshield-production-media",
        "billing_subject_secret": "b" * 64,
    }
    values.update(overrides)
    return values


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"jwt_secret": "change-me"}, "jwt_secret"),
        ({"database_url": "postgresql+asyncpg://app:change-me@localhost/db"}, "database_url"),
        ({"smtp_password": None}, "SMTP credentials"),
        ({"push_provider_token": None}, "push provider credentials"),
        ({"tow_provider_token": None}, "tow lookup provider credentials"),
        ({"media_bucket": None}, "media_bucket"),
        ({"media_bucket": "   "}, "media_bucket"),
        ({"push_provider_url": "http://push.example.net"}, "push provider URL"),
        ({"tow_provider_url": "http://tow.example.net"}, "tow lookup provider URL"),
        ({"billing_subject_secret": "change-me"}, "billing_subject_secret"),
        ({"billing_enabled": True}, "billing verification gateway credentials"),
        (
            {
                "billing_enabled": True,
                "billing_gateway_url": "http://billing.example.net/verify",
                "billing_gateway_token": "token",
                "apple_premium_product_id": "ai.parkshield.premium",
            },
            "billing verification gateway URL",
        ),
        (
            {
                "billing_enabled": True,
                "billing_gateway_url": "https://billing.example.net/verify",
                "billing_gateway_token": "token",
            },
            "store product ID",
        ),
        (
            {"observability_export_enabled": True},
            "observability export requires",
        ),
        (
            {
                "observability_export_enabled": True,
                "observability_provider": "opentelemetry",
                "observability_otlp_endpoint": "http://collector.example.net",
            },
            "observability OTLP endpoint",
        ),
        (
            {"product_analytics_enabled": True},
            "product analytics requires",
        ),
        (
            {
                "product_analytics_enabled": True,
                "product_analytics_provider": "memory",
            },
            "external provider",
        ),
        (
            {
                "product_analytics_enabled": True,
                "product_analytics_provider": "external",
            },
            "product_analytics_subject_secret",
        ),
    ],
)
def test_deployed_configuration_fails_fast(
    overrides: dict[str, object], message: str
) -> None:
    with pytest.raises(ValidationError, match=message):
        Settings(**deployed_settings(**overrides))


def test_local_configuration_keeps_safe_development_defaults() -> None:
    assert Settings(environment="local").environment == "local"


def test_deployed_configuration_accepts_disabled_billing_and_valid_providers() -> None:
    disabled = Settings(**deployed_settings())
    enabled = Settings(
        **deployed_settings(
            billing_enabled=True,
            billing_gateway_url="https://billing.example.net/verify",
            billing_gateway_token="synthetic-provider-token",
            apple_premium_product_id="ai.parkshield.synthetic.premium",
        )
    )
    assert disabled.billing_enabled is False
    assert enabled.billing_enabled is True


def test_deployed_configuration_accepts_approved_observability_settings() -> None:
    settings = Settings(
        **deployed_settings(
            observability_export_enabled=True,
            observability_provider="opentelemetry",
            observability_otlp_endpoint="https://collector.example.net/v1/traces",
            product_analytics_enabled=True,
            product_analytics_provider="external",
            product_analytics_subject_secret="c" * 64,
        )
    )

    assert settings.observability_export_enabled is True
    assert settings.product_analytics_enabled is True


def test_access_log_is_structured_and_excludes_query_and_headers(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="parkshield.http")
    with TestClient(create_app()) as client:
        response = client.get(
            "/api/v1/health/live?access_token=must-not-be-logged",
            headers={
                "Authorization": "Bearer must-not-be-logged",
                "X-Request-ID": "observability-1",
            },
        )

    record = next(record for record in caplog.records if "http_request_completed" in record.message)
    payload = json.loads(record.message)
    assert response.status_code == 200
    assert payload["request_id"] == "observability-1"
    assert payload["status_code"] == 200
    assert payload["category"] == "health"
    assert "path" not in payload
    assert "must-not-be-logged" not in record.message


def test_untrusted_request_id_is_replaced() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/health/live", headers={"X-Request-ID": "bad id\nvalue"})
    assert response.headers["X-Request-ID"] != "bad id\nvalue"
