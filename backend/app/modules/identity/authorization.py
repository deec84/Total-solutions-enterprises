"""Role-based authorization policy independent of HTTP and persistence."""

from collections.abc import Collection

from app.modules.identity.domain import Role, User


class AuthorizationError(PermissionError):
    pass


def authorize(user: User, allowed_roles: Collection[Role]) -> None:
    """Require an active user whose role is explicitly allowed; deny by default."""
    if not user.is_active or user.role not in allowed_roles:
        raise AuthorizationError("insufficient permissions")
