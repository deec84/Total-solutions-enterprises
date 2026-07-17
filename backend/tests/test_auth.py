"""Authentication API contract and session lifecycle tests."""

from collections.abc import Iterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.modules.identity.audit import AuditAction, InMemoryAuditSink
from app.modules.identity.repositories import InMemoryVerificationNotifier
from app.modules.identity.service import IdentityService
from app.presentation.api.routes.auth import build_identity_service, get_identity_service


@pytest.fixture
def notifier() -> InMemoryVerificationNotifier:
    return InMemoryVerificationNotifier()


@pytest.fixture
def audit() -> InMemoryAuditSink:
    return InMemoryAuditSink()


@pytest.fixture
def identity_service(
    notifier: InMemoryVerificationNotifier, audit: InMemoryAuditSink
) -> IdentityService:
    return build_identity_service(notifier, audit)


@pytest.fixture
def api(identity_service: IdentityService) -> Iterator[TestClient]:
    """Provide one isolated repository graph shared by every request in a test."""
    application = create_app()
    application.dependency_overrides[get_identity_service] = lambda: identity_service
    with TestClient(application) as test_client:
        yield test_client
    application.dependency_overrides.clear()


def verify_registered_email(
    api: TestClient, notifier: InMemoryVerificationNotifier, email: str
) -> None:
    response = api.post(
        "/api/v1/auth/verify-email", json={"token": notifier.token_for(email)}
    )
    assert response.status_code == 200
    assert response.json()["is_verified"] is True


def test_registration_login_and_current_user(
    api: TestClient, notifier: InMemoryVerificationNotifier
) -> None:
    registration = api.post(
        "/api/v1/auth/register",
        json={"email": " Driver@Example.com ", "password": "a-secure-password"},
    )
    verify_registered_email(api, notifier, "driver@example.com")
    login = api.post(
        "/api/v1/auth/login",
        json={"email": "driver@example.com", "password": "a-secure-password"},
    )
    profile = api.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )

    assert registration.status_code == 201
    assert registration.json()["email"] == "driver@example.com"
    assert login.status_code == 200
    assert profile.status_code == 200
    assert profile.json()["role"] == "user"


def test_duplicate_registration_and_bad_login_do_not_leak_details(api: TestClient) -> None:
    payload = {"email": "driver@example.com", "password": "a-secure-password"}
    assert api.post("/api/v1/auth/register", json=payload).status_code == 201
    duplicate = api.post("/api/v1/auth/register", json=payload)
    bad_login = api.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": "incorrect-password"},
    )

    assert duplicate.status_code == 409
    assert bad_login.status_code == 401
    assert bad_login.json()["detail"] == "invalid credentials"


def test_refresh_tokens_rotate_and_logout_revokes_session(
    api: TestClient, notifier: InMemoryVerificationNotifier
) -> None:
    credentials = {"email": "driver@example.com", "password": "a-secure-password"}
    api.post("/api/v1/auth/register", json=credentials)
    verify_registered_email(api, notifier, credentials["email"])
    original = api.post("/api/v1/auth/login", json=credentials).json()["refresh_token"]
    rotated_response = api.post("/api/v1/auth/refresh", json={"refresh_token": original})
    replay = api.post("/api/v1/auth/refresh", json={"refresh_token": original})
    rotated = rotated_response.json()["refresh_token"]
    logout = api.post("/api/v1/auth/logout", json={"refresh_token": rotated})
    after_logout = api.post("/api/v1/auth/refresh", json={"refresh_token": rotated})

    assert rotated_response.status_code == 200
    assert replay.status_code == 401
    assert logout.status_code == 204
    assert after_logout.status_code == 401


def test_rejects_missing_access_token_and_weak_registration_password(api: TestClient) -> None:
    profile = api.get("/api/v1/auth/me")
    weak = api.post(
        "/api/v1/auth/register",
        json={"email": "driver@example.com", "password": "short"},
    )

    assert profile.status_code == 401
    assert weak.status_code == 422


def test_unverified_account_cannot_login(
    api: TestClient, notifier: InMemoryVerificationNotifier
) -> None:
    credentials = {"email": "pending@example.com", "password": "a-secure-password"}
    registration = api.post("/api/v1/auth/register", json=credentials)
    login = api.post("/api/v1/auth/login", json=credentials)

    assert registration.status_code == 201
    assert registration.json()["is_verified"] is False
    assert notifier.token_for(credentials["email"])
    assert login.status_code == 401


def test_rejects_invalid_verification_token(api: TestClient) -> None:
    response = api.post("/api/v1/auth/verify-email", json={"token": "invalid"})

    assert response.status_code == 400
    assert response.json()["detail"] == "invalid verification token"


def test_password_reset_is_single_use_and_revokes_existing_sessions(
    api: TestClient, notifier: InMemoryVerificationNotifier
) -> None:
    email = "recover@example.com"
    old_credentials = {"email": email, "password": "old-secure-password"}
    api.post("/api/v1/auth/register", json=old_credentials)
    verify_registered_email(api, notifier, email)
    existing_refresh = api.post("/api/v1/auth/login", json=old_credentials).json()[
        "refresh_token"
    ]

    request = api.post("/api/v1/auth/password-reset/request", json={"email": email})
    token = notifier.password_reset_token_for(email)
    confirmation = api.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": token, "new_password": "new-secure-password"},
    )
    replay = api.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": token, "new_password": "another-password"},
    )
    stale_session = api.post(
        "/api/v1/auth/refresh", json={"refresh_token": existing_refresh}
    )
    old_login = api.post("/api/v1/auth/login", json=old_credentials)
    new_login = api.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "new-secure-password"},
    )

    assert request.status_code == 200
    assert confirmation.status_code == 200
    assert replay.status_code == 400
    assert stale_session.status_code == 401
    assert old_login.status_code == 401
    assert new_login.status_code == 200


def test_password_reset_request_does_not_disclose_unknown_accounts(api: TestClient) -> None:
    response = api.post(
        "/api/v1/auth/password-reset/request", json={"email": "missing@example.com"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "If the account exists, reset instructions were sent."
    }


def test_login_rate_limit_is_scoped_and_returns_retry_after(api: TestClient) -> None:
    for _ in range(5):
        response = api.post(
            "/api/v1/auth/login",
            json={"email": "target@example.com", "password": "incorrect-password"},
        )
        assert response.status_code == 401

    blocked = api.post(
        "/api/v1/auth/login",
        json={"email": "target@example.com", "password": "incorrect-password"},
    )
    different_identity = api.post(
        "/api/v1/auth/login",
        json={"email": "other@example.com", "password": "incorrect-password"},
    )

    assert blocked.status_code == 429
    assert int(blocked.headers["Retry-After"]) > 0
    assert blocked.json()["detail"] == "too many authentication attempts"
    assert different_identity.status_code == 401


def test_security_lifecycle_emits_structured_audit_events(
    api: TestClient,
    notifier: InMemoryVerificationNotifier,
    audit: InMemoryAuditSink,
) -> None:
    credentials = {"email": "audit@example.com", "password": "a-secure-password"}
    api.post("/api/v1/auth/register", json=credentials)
    verify_registered_email(api, notifier, credentials["email"])
    tokens = api.post("/api/v1/auth/login", json=credentials).json()
    api.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})

    actions = [item.action for item in audit.events()]
    assert actions == [
        AuditAction.USER_REGISTERED,
        AuditAction.EMAIL_VERIFIED,
        AuditAction.LOGIN_SUCCEEDED,
        AuditAction.TOKEN_REFRESHED,
    ]
    assert all(item.subject_id is not None for item in audit.events())


def test_user_lists_and_revokes_only_owned_sessions(
    api: TestClient, notifier: InMemoryVerificationNotifier
) -> None:
    credentials = {"email": "sessions@example.com", "password": "a-secure-password"}
    api.post("/api/v1/auth/register", json=credentials)
    verify_registered_email(api, notifier, credentials["email"])
    first = api.post("/api/v1/auth/login", json=credentials).json()
    api.post("/api/v1/auth/login", json=credentials)
    headers = {"Authorization": f"Bearer {first['access_token']}"}

    before = api.get("/api/v1/auth/sessions", headers=headers)
    session_id = before.json()[0]["id"]
    revoked = api.delete(f"/api/v1/auth/sessions/{session_id}", headers=headers)
    after = api.get("/api/v1/auth/sessions", headers=headers)
    unknown = api.delete(f"/api/v1/auth/sessions/{uuid4()}", headers=headers)

    assert before.status_code == 200
    assert len(before.json()) == 2
    assert revoked.status_code == 204
    assert len(after.json()) == 1
    assert unknown.status_code == 404
