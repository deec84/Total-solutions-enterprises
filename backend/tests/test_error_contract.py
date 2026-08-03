"""Contract tests for the versioned public API error envelope."""

import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from httpx import Response

from app.main import create_app
from app.modules.identity.audit import InMemoryAuditSink
from app.modules.identity.repositories import InMemoryVerificationNotifier
from app.presentation.api.routes.auth import build_identity_service, get_identity_service


@pytest.fixture
def api() -> Iterator[TestClient]:
    application = create_app()
    service = build_identity_service(InMemoryVerificationNotifier(), InMemoryAuditSink())
    application.dependency_overrides[get_identity_service] = lambda: service
    with TestClient(application, raise_server_exceptions=False) as test_client:
        yield test_client
    application.dependency_overrides.clear()


def assert_error_envelope(response: Response, status_code: int, code: str) -> None:
    assert response.status_code == status_code
    payload = response.json()
    assert payload["version"] == "1"
    assert payload["code"] == code
    assert payload["message"]
    assert payload["correlation_id"]
    assert "detail" not in payload


def test_login_401_uses_stable_safe_code(api: TestClient) -> None:
    response = api.post(
        "/api/v1/auth/login",
        json={"email": "person@example.com", "password": "not-the-password"},
        headers={"X-Correlation-ID": "contract-login-401"},
    )

    assert_error_envelope(response, 401, "AUTHENTICATION_FAILED")
    assert response.json()["correlation_id"] == "contract-login-401"
    assert "person@example.com" not in response.text
    assert "not-the-password" not in response.text


def test_login_429_preserves_retry_after_and_safe_code(api: TestClient) -> None:
    for _ in range(5):
        api.post(
            "/api/v1/auth/login",
            json={"email": "limited@example.com", "password": "not-the-password"},
        )

    response = api.post(
        "/api/v1/auth/login",
        json={"email": "limited@example.com", "password": "not-the-password"},
    )

    assert_error_envelope(response, 429, "RATE_LIMITED")
    assert int(response.headers["Retry-After"]) > 0


def test_refresh_401_uses_session_code(api: TestClient) -> None:
    response = api.post("/api/v1/auth/refresh", json={"refresh_token": "not-a-real-token"})

    assert_error_envelope(response, 401, "SESSION_INVALID")
    assert "not-a-real-token" not in response.text


def test_authorization_403_uses_stable_code(api: TestClient) -> None:
    async def forbidden() -> None:
        raise HTTPException(status_code=403, detail="internal authorization reason")

    api.app.add_api_route("/api/v1/contract/forbidden", forbidden)
    response = api.get("/api/v1/contract/forbidden")

    assert_error_envelope(response, 403, "AUTHORIZATION_DENIED")
    assert "internal authorization reason" not in response.text


def test_validation_422_filters_input_and_uses_allowlisted_details(api: TestClient) -> None:
    response = api.post("/api/v1/auth/login", json={"email": "person@example.com"})

    assert_error_envelope(response, 422, "VALIDATION_FAILED")
    assert response.json()["details"] == [{"field": "password", "code": "MISSING_FIELD"}]
    assert "person@example.com" not in response.text


def test_unhandled_error_is_sanitized(api: TestClient) -> None:
    async def failure() -> None:
        raise RuntimeError("postgres://operator:password@example.test/private/path token=secret")

    api.app.add_api_route("/api/v1/contract/failure", failure)
    response = api.get("/api/v1/contract/failure")

    assert_error_envelope(response, 500, "INTERNAL_ERROR")
    assert "postgres" not in response.text
    assert "password" not in response.text
    assert "secret" not in response.text


def test_openapi_declares_error_envelope_for_authentication_routes(api: TestClient) -> None:
    schema = api.app.openapi()
    assert "ErrorResponse" in schema["components"]["schemas"]
    for path, expected_statuses in {
        "/api/v1/auth/login": {"401", "422", "429", "500"},
        "/api/v1/auth/refresh": {"401", "422", "500"},
        "/api/v1/auth/me": {"401", "500"},
    }.items():
        responses = schema["paths"][path][next(iter(schema["paths"][path]))]["responses"]
        assert expected_statuses <= set(responses)
        for status_code in expected_statuses:
            assert responses[status_code]["content"]["application/json"]["schema"] == {
                "$ref": "#/components/schemas/ErrorResponse"
            }


def test_versioned_openapi_snapshot_matches_current_contract(api: TestClient) -> None:
    snapshot = Path(__file__).resolve().parents[2] / "contracts/openapi/parkshield-api.v1.json"
    assert api.app.openapi() == json.loads(snapshot.read_text(encoding="utf-8"))
