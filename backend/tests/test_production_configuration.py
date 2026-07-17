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
        ({"push_provider_url": "http://push.example.net"}, "push provider URL"),
        ({"tow_provider_url": "http://tow.example.net"}, "tow lookup provider URL"),
    ],
)
def test_deployed_configuration_fails_fast(
    overrides: dict[str, object], message: str
) -> None:
    with pytest.raises(ValidationError, match=message):
        Settings(**deployed_settings(**overrides))


def test_local_configuration_keeps_safe_development_defaults() -> None:
    assert Settings(environment="local").environment == "local"


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
    assert payload["path"] == "/api/v1/health/live"
    assert "must-not-be-logged" not in record.message


def test_untrusted_request_id_is_replaced() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/health/live", headers={"X-Request-ID": "bad id\nvalue"})
    assert response.headers["X-Request-ID"] != "bad id\nvalue"
