"""Password and JWT primitives isolated from identity use cases."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import UUID, uuid4

import jwt
from pwdlib import PasswordHash

from app.modules.identity.domain import Role


class InvalidTokenError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class TokenClaims:
    subject: UUID
    role: Role
    token_id: UUID
    token_type: Literal["access", "refresh"]
    expires_at: datetime


class PasswordManager:
    def __init__(self) -> None:
        self._password_hash = PasswordHash.recommended()

    def hash(self, password: str) -> str:
        return self._password_hash.hash(password)

    def verify(self, password: str, password_hash: str) -> bool:
        return self._password_hash.verify(password, password_hash)


class TokenManager:
    def __init__(self, secret: str, access_minutes: int, refresh_days: int) -> None:
        if len(secret) < 32:
            raise ValueError("JWT secret must contain at least 32 characters")
        self._secret = secret
        self._access_ttl = timedelta(minutes=access_minutes)
        self._refresh_ttl = timedelta(days=refresh_days)

    @property
    def access_ttl_seconds(self) -> int:
        return int(self._access_ttl.total_seconds())

    def create(
        self, subject: UUID, role: Role, token_type: Literal["access", "refresh"]
    ) -> tuple[str, TokenClaims]:
        now = datetime.now(UTC)
        expires_at = now + (self._access_ttl if token_type == "access" else self._refresh_ttl)
        claims = TokenClaims(subject, role, uuid4(), token_type, expires_at)
        payload: dict[str, Any] = {
            "sub": str(subject),
            "role": role.value,
            "jti": str(claims.token_id),
            "type": token_type,
            "iat": now,
            "exp": expires_at,
            "iss": "parkshield-api",
        }
        return jwt.encode(payload, self._secret, algorithm="HS256"), claims

    def decode(self, token: str, expected_type: Literal["access", "refresh"]) -> TokenClaims:
        try:
            payload = jwt.decode(
                token, self._secret, algorithms=["HS256"], issuer="parkshield-api"
            )
            if payload.get("type") != expected_type:
                raise InvalidTokenError("unexpected token type")
            return TokenClaims(
                subject=UUID(payload["sub"]),
                role=Role(payload["role"]),
                token_id=UUID(payload["jti"]),
                token_type=expected_type,
                expires_at=datetime.fromtimestamp(payload["exp"], tz=UTC),
            )
        except (jwt.PyJWTError, KeyError, ValueError) as error:
            raise InvalidTokenError("invalid or expired token") from error


class VerificationTokenManager:
    def __init__(self, secret: str, ttl_hours: int = 24) -> None:
        if len(secret) < 32:
            raise ValueError("JWT secret must contain at least 32 characters")
        self._secret = secret
        self._ttl = timedelta(hours=ttl_hours)

    def create(self, user_id: UUID) -> str:
        now = datetime.now(UTC)
        return jwt.encode(
            {
                "sub": str(user_id),
                "type": "verify_email",
                "iat": now,
                "exp": now + self._ttl,
                "iss": "parkshield-api",
            },
            self._secret,
            algorithm="HS256",
        )

    def decode(self, token: str) -> UUID:
        try:
            payload = jwt.decode(
                token, self._secret, algorithms=["HS256"], issuer="parkshield-api"
            )
            if payload.get("type") != "verify_email":
                raise InvalidTokenError("unexpected token type")
            return UUID(payload["sub"])
        except (jwt.PyJWTError, KeyError, ValueError) as error:
            raise InvalidTokenError("invalid or expired verification token") from error


@dataclass(frozen=True, slots=True)
class PasswordResetClaims:
    user_id: UUID
    token_id: UUID
    expires_at: datetime


class PasswordResetTokenManager:
    def __init__(self, secret: str, ttl_minutes: int = 30) -> None:
        if len(secret) < 32:
            raise ValueError("JWT secret must contain at least 32 characters")
        self._secret = secret
        self._ttl = timedelta(minutes=ttl_minutes)

    def create(self, user_id: UUID) -> tuple[str, PasswordResetClaims]:
        now = datetime.now(UTC)
        claims = PasswordResetClaims(user_id, uuid4(), now + self._ttl)
        token = jwt.encode(
            {
                "sub": str(user_id),
                "jti": str(claims.token_id),
                "type": "reset_password",
                "iat": now,
                "exp": claims.expires_at,
                "iss": "parkshield-api",
            },
            self._secret,
            algorithm="HS256",
        )
        return token, claims

    def decode(self, token: str) -> PasswordResetClaims:
        try:
            payload = jwt.decode(
                token, self._secret, algorithms=["HS256"], issuer="parkshield-api"
            )
            if payload.get("type") != "reset_password":
                raise InvalidTokenError("unexpected token type")
            return PasswordResetClaims(
                UUID(payload["sub"]),
                UUID(payload["jti"]),
                datetime.fromtimestamp(payload["exp"], tz=UTC),
            )
        except (jwt.PyJWTError, KeyError, ValueError) as error:
            raise InvalidTokenError("invalid or expired password reset token") from error
