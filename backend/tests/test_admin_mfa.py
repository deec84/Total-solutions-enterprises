import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.modules.identity.domain import Role, User
from app.modules.identity.mfa import (
    decrypt_secret,
    encrypt_secret,
    generate_secret,
    provisioning_uri,
    totp,
    verify_totp,
)
from app.modules.identity.repositories import InMemoryUserRepository
from app.presentation.api.routes.admin import overview, privileged_user


def test_totp_matches_rfc_vector_and_accepts_small_clock_drift() -> None:
    secret = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
    assert totp(secret, 59) == "287082"
    assert verify_totp(secret, "287082", 59)
    assert verify_totp(secret, totp(secret, 30), 59)
    assert not verify_totp(secret, "invalid", 59)


def test_mfa_secret_and_provisioning_uri_are_authenticator_compatible() -> None:
    secret = generate_secret()
    uri = provisioning_uri(secret, "admin@example.com")
    assert len(secret) == 32
    assert uri.startswith("otpauth://totp/ParkShield%20AI%3Aadmin%40example.com")
    assert f"secret={secret}" in uri


def test_mfa_secret_is_authenticated_and_encrypted_at_rest() -> None:
    secret = generate_secret()
    ciphertext = encrypt_secret(secret, "application-secret-with-enough-entropy")
    assert secret not in ciphertext
    assert decrypt_secret(ciphertext, "application-secret-with-enough-entropy") == secret
    with pytest.raises(ValueError):
        decrypt_secret(ciphertext, "a-different-application-secret")


def test_privileged_dependency_requires_enrollment_and_valid_code() -> None:
    async def scenario() -> None:
        base = User(
            uuid4(), "admin@example.com", "hash", Role.ADMIN, True, True, datetime.now(UTC)
        )
        with pytest.raises(HTTPException) as enrollment:
            await privileged_user(base, None)
        assert enrollment.value.status_code == 403

        secret = generate_secret()
        enrolled = User(
            base.id,
            base.email,
            base.password_hash,
            base.role,
            base.is_active,
            base.is_verified,
            base.created_at,
            secret,
            True,
        )
        with pytest.raises(HTTPException) as invalid:
            await privileged_user(enrolled, "000000")
        assert invalid.value.status_code == 401
        assert await privileged_user(enrolled, totp(secret)) == enrolled

    asyncio.run(scenario())


def test_in_memory_repository_persists_mfa_state_per_user() -> None:
    async def scenario() -> None:
        repository = InMemoryUserRepository()
        user = User(
            uuid4(), "moderator@example.com", "hash", Role.MODERATOR, True, True, datetime.now(UTC)
        )
        await repository.add(user)
        updated = await repository.set_mfa(user.id, "SECRET", True)
        assert updated is not None and updated.mfa_enabled
        assert await repository.set_mfa(uuid4(), "SECRET", True) is None

    asyncio.run(scenario())


def test_admin_overview_aggregates_operational_counts() -> None:
    async def scenario() -> None:
        session = AsyncMock()
        session.scalar.side_effect = [8, 3]
        rows = Mock()
        rows.tuples.return_value = iter(
            [("pending", 2), ("published", 12), ("rejected", 1)]
        )
        session.execute.return_value = rows
        user = User(
            uuid4(), "admin@example.com", "hash", Role.ADMIN, True, True, datetime.now(UTC)
        )
        result = await overview(user, session)
        assert result.users == 8
        assert result.active_sessions == 3
        assert result.pending_reports == 2
        assert result.published_reports == 12

    asyncio.run(scenario())
