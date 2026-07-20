"""Privacy rights, minimization, and fail-closed deletion tests."""

import asyncio
from collections.abc import Iterator
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import create_app
from app.modules.identity.domain import Role, User
from app.modules.identity.security import PasswordManager
from app.modules.privacy.domain import ConsentPurpose, DataRequestStatus
from app.modules.privacy.repositories import InMemoryPrivacyRepository
from app.modules.privacy.service import (
    ACCOUNT_DELETION_CONFIRMATION,
    ExternalDataDeletionError,
    PrivacyRequestError,
    PrivacyService,
)
from app.presentation.api.routes.auth import current_user
from app.presentation.api.routes.privacy import privacy_service


class RecordingMediaStore:
    def __init__(self, fail: bool = False) -> None:
        self.deleted: list[str] = []
        self.fail = fail

    async def delete(self, key: str) -> None:
        if self.fail:
            raise RuntimeError("provider unavailable")
        self.deleted.append(key)


class MissingAccountRepository(InMemoryPrivacyRepository):
    async def delete_account(self, user_id: UUID) -> bool:
        return False


class RecordingAnalyticsStore:
    def __init__(self, fail: bool = False) -> None:
        self.deleted: list[UUID] = []
        self.fail = fail

    def delete_user(self, user_id: UUID) -> int:
        if self.fail:
            raise RuntimeError("analytics provider unavailable")
        self.deleted.append(user_id)
        return 1


def user(passwords: PasswordManager, role: Role = Role.USER, mfa: bool = False) -> User:
    return User(
        uuid4(),
        "privacy@example.com",
        passwords.hash("a-secure-password"),
        role,
        True,
        True,
        datetime.now(UTC),
        "JBSWY3DPEHPK3PXP" if mfa else None,
        mfa,
    )


def service(
    repository: InMemoryPrivacyRepository,
    passwords: PasswordManager,
    store: RecordingMediaStore | None = None,
) -> PrivacyService:
    return PrivacyService(repository, passwords, "test-subject-secret", "policy-v1", store)


def test_consent_history_returns_only_latest_decision_per_purpose() -> None:
    async def scenario() -> None:
        repository = InMemoryPrivacyRepository()
        passwords = PasswordManager()
        subject = user(passwords)
        privacy = service(repository, passwords)

        first = await privacy.decide_consent(
            subject.id, ConsentPurpose.PRODUCT_ANALYTICS, True
        )
        latest = await privacy.decide_consent(
            subject.id, ConsentPurpose.PRODUCT_ANALYTICS, False
        )
        personalized = await privacy.decide_consent(
            subject.id, ConsentPurpose.PERSONALIZED_RECOMMENDATIONS, True
        )

        decisions = await privacy.consents(subject.id)
        assert first.policy_version == "policy-v1"
        assert decisions == (personalized, latest)

    asyncio.run(scenario())


def test_export_records_completed_request_and_returns_minimized_snapshot() -> None:
    async def scenario() -> None:
        repository = InMemoryPrivacyRepository(
            {"profile": {"email": "privacy@example.com"}, "sessions": []}
        )
        passwords = PasswordManager()
        subject = user(passwords)
        export = await service(repository, passwords).export(subject.id)

        assert export.policy_version == "policy-v1"
        assert export.data["profile"] == {"email": "privacy@example.com"}
        request = repository.request(export.request_id)
        assert request.status is DataRequestStatus.COMPLETED
        assert request.completed_at is not None
        assert len(request.subject_reference) == 64
        assert str(subject.id) not in request.subject_reference

    asyncio.run(scenario())


def test_account_deletion_verifies_credentials_and_deletes_private_media() -> None:
    async def scenario() -> None:
        key = f"community-reports/{uuid4()}/{'a' * 64}"
        repository = InMemoryPrivacyRepository(media_keys=(key,))
        passwords = PasswordManager()
        subject = user(passwords)
        store = RecordingMediaStore()

        request_id = await service(repository, passwords, store).delete_account(
            subject,
            "a-secure-password",
            ACCOUNT_DELETION_CONFIRMATION,
        )

        assert store.deleted == [key]
        assert repository.deleted(subject.id)
        assert repository.request(request_id).status is DataRequestStatus.COMPLETED

    asyncio.run(scenario())


def test_account_deletion_removes_analytics_and_fails_closed_on_provider_error() -> None:
    async def scenario() -> None:
        passwords = PasswordManager()
        subject = user(passwords)
        accepted_repository = InMemoryPrivacyRepository()
        analytics = RecordingAnalyticsStore()
        privacy = PrivacyService(
            accepted_repository,
            passwords,
            "test-subject-secret",
            "policy-v1",
            analytics_store=analytics,
        )
        await privacy.delete_account(
            subject,
            "a-secure-password",
            ACCOUNT_DELETION_CONFIRMATION,
        )
        assert analytics.deleted == [subject.id]
        assert accepted_repository.deleted(subject.id)

        rejected_repository = InMemoryPrivacyRepository()
        rejected_subject = user(passwords)
        failing = PrivacyService(
            rejected_repository,
            passwords,
            "test-subject-secret",
            "policy-v1",
            analytics_store=RecordingAnalyticsStore(fail=True),
        )
        with pytest.raises(ExternalDataDeletionError, match="analytics deletion"):
            await failing.delete_account(
                rejected_subject,
                "a-secure-password",
                ACCOUNT_DELETION_CONFIRMATION,
            )
        assert not rejected_repository.deleted(rejected_subject.id)

    asyncio.run(scenario())


def test_account_deletion_rejects_unsafe_requests() -> None:
    async def scenario() -> None:
        passwords = PasswordManager()
        repository = InMemoryPrivacyRepository()
        privacy = service(repository, passwords)
        subject = user(passwords)

        with pytest.raises(PrivacyRequestError, match="confirmation"):
            await privacy.delete_account(subject, "a-secure-password", "DELETE")
        with pytest.raises(PrivacyRequestError, match="credentials"):
            await privacy.delete_account(
                subject, "wrong-password", ACCOUNT_DELETION_CONFIRMATION
            )
        with pytest.raises(PrivacyRequestError, match="offboarding"):
            await privacy.delete_account(
                user(passwords, Role.ADMIN),
                "a-secure-password",
                ACCOUNT_DELETION_CONFIRMATION,
            )
        with pytest.raises(PrivacyRequestError, match="MFA"):
            await privacy.delete_account(
                user(passwords, mfa=True),
                "a-secure-password",
                ACCOUNT_DELETION_CONFIRMATION,
            )

        mfa_user = user(passwords, mfa=True)
        with patch("app.modules.privacy.service.verify_totp", return_value=True):
            await privacy.delete_account(
                mfa_user,
                "a-secure-password",
                ACCOUNT_DELETION_CONFIRMATION,
                "123456",
            )
        assert repository.deleted(mfa_user.id)

    asyncio.run(scenario())


def test_account_deletion_fails_closed_when_private_media_cannot_be_removed() -> None:
    async def scenario() -> None:
        key = f"community-reports/{uuid4()}/{'b' * 64}"
        passwords = PasswordManager()
        subject = user(passwords)

        unavailable = InMemoryPrivacyRepository(media_keys=(key,))
        with pytest.raises(ExternalDataDeletionError, match="unavailable"):
            await service(unavailable, passwords).delete_account(
                subject,
                "a-secure-password",
                ACCOUNT_DELETION_CONFIRMATION,
            )
        assert not unavailable.deleted(subject.id)

        failed = InMemoryPrivacyRepository(media_keys=(key,))
        with pytest.raises(ExternalDataDeletionError, match="could not be confirmed"):
            await service(failed, passwords, RecordingMediaStore(fail=True)).delete_account(
                subject,
                "a-secure-password",
                ACCOUNT_DELETION_CONFIRMATION,
            )
        assert not failed.deleted(subject.id)

    asyncio.run(scenario())


def test_account_deletion_fails_if_the_transaction_cannot_find_the_account() -> None:
    async def scenario() -> None:
        passwords = PasswordManager()
        subject = user(passwords)
        with pytest.raises(PrivacyRequestError, match="no longer exists"):
            await service(MissingAccountRepository(), passwords).delete_account(
                subject,
                "a-secure-password",
                ACCOUNT_DELETION_CONFIRMATION,
            )

    asyncio.run(scenario())


@pytest.fixture
def privacy_api() -> Iterator[tuple[TestClient, InMemoryPrivacyRepository, User]]:
    passwords = PasswordManager()
    subject = user(passwords)
    repository = InMemoryPrivacyRepository(
        {"profile": {"email": subject.email}, "push_devices": []}
    )
    application = create_app()
    application.dependency_overrides[current_user] = lambda: subject
    application.dependency_overrides[privacy_service] = lambda: service(
        repository, passwords
    )
    with TestClient(application) as client:
        yield client, repository, subject
    application.dependency_overrides.clear()


def test_privacy_api_consent_export_and_account_deletion(
    privacy_api: tuple[TestClient, InMemoryPrivacyRepository, User],
) -> None:
    client, repository, subject = privacy_api
    granted = client.put(
        "/api/v1/privacy/consents/product_analytics", json={"granted": True}
    )
    listed = client.get("/api/v1/privacy/consents")
    export = client.post("/api/v1/privacy/export")
    deletion = client.request(
        "DELETE",
        "/api/v1/privacy/account",
        json={
            "password": "a-secure-password",
            "confirmation": ACCOUNT_DELETION_CONFIRMATION,
        },
    )

    assert granted.status_code == 200
    assert granted.json()["policy_version"] == "policy-v1"
    assert listed.json()[0]["granted"] is True
    assert export.status_code == 200
    assert export.headers["cache-control"] == "private, no-store"
    assert export.headers["pragma"] == "no-cache"
    assert "password_hash" not in export.text
    assert deletion.status_code == 204
    assert deletion.headers["clear-site-data"] == '"cache", "storage"'
    assert repository.deleted(subject.id)


def test_privacy_api_rejects_invalid_purpose_confirmation_and_password(
    privacy_api: tuple[TestClient, InMemoryPrivacyRepository, User],
) -> None:
    client, _, _ = privacy_api
    unknown = client.put(
        "/api/v1/privacy/consents/advertising", json={"granted": True}
    )
    bad_confirmation = client.request(
        "DELETE",
        "/api/v1/privacy/account",
        json={"password": "a-secure-password", "confirmation": "DELETE"},
    )
    bad_password = client.request(
        "DELETE",
        "/api/v1/privacy/account",
        json={
            "password": "wrong-password",
            "confirmation": ACCOUNT_DELETION_CONFIRMATION,
        },
    )

    assert unknown.status_code == 422
    assert bad_confirmation.status_code == 422
    assert bad_password.status_code == 403


def test_privacy_api_fails_closed_when_media_storage_is_unavailable() -> None:
    passwords = PasswordManager()
    subject = user(passwords)
    repository = InMemoryPrivacyRepository(
        media_keys=(f"community-reports/{uuid4()}/{'a' * 64}",)
    )
    application = create_app()
    application.dependency_overrides[current_user] = lambda: subject
    application.dependency_overrides[privacy_service] = lambda: service(
        repository, passwords
    )
    with TestClient(application) as client:
        response = client.request(
            "DELETE",
            "/api/v1/privacy/account",
            json={
                "password": "a-secure-password",
                "confirmation": ACCOUNT_DELETION_CONFIRMATION,
            },
        )
    assert response.status_code == 503
    assert not repository.deleted(subject.id)


def test_privacy_service_dependency_builds_sql_adapter() -> None:
    application = create_app()
    request = SimpleNamespace(app=application)
    built = privacy_service(AsyncMock(spec=AsyncSession), request)  # type: ignore[arg-type]
    assert isinstance(built, PrivacyService)
