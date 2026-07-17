"""RBAC policy tests."""

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.modules.identity.authorization import AuthorizationError, authorize
from app.modules.identity.domain import Role, User
from app.presentation.api.routes.auth import require_roles


def user(role: Role, *, active: bool = True) -> User:
    return User(uuid4(), "person@example.com", "unused", role, active, True, datetime.now(UTC))


def test_allows_an_explicit_role() -> None:
    authorize(user(Role.ADMIN), {Role.ADMIN})


@pytest.mark.parametrize("candidate", [Role.USER, Role.MODERATOR])
def test_denies_roles_not_in_policy(candidate: Role) -> None:
    with pytest.raises(AuthorizationError, match="insufficient permissions"):
        authorize(user(candidate), {Role.ADMIN})


def test_denies_inactive_user_even_when_role_matches() -> None:
    with pytest.raises(AuthorizationError, match="insufficient permissions"):
        authorize(user(Role.ADMIN, active=False), {Role.ADMIN})


def test_http_role_dependency_returns_user_or_403() -> None:
    async def scenario() -> None:
        dependency = require_roles(Role.ADMIN)
        admin = user(Role.ADMIN)
        assert await dependency(admin) is admin
        with pytest.raises(HTTPException) as denied:
            await dependency(user(Role.USER))
        assert denied.value.status_code == 403

    asyncio.run(scenario())
