"""Identity application service."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.modules.identity.abuse import LoginRateLimiter
from app.modules.identity.audit import AuditAction, AuditSink, event
from app.modules.identity.domain import (
    Role,
    Session,
    SessionRepository,
    User,
    UserRepository,
    VerificationNotifier,
)
from app.modules.identity.schemas import TokenPair
from app.modules.identity.security import (
    InvalidTokenError,
    PasswordManager,
    PasswordResetTokenManager,
    TokenManager,
    VerificationTokenManager,
)


class AuthenticationError(ValueError):
    pass


class IdentityService:
    def __init__(
        self,
        users: UserRepository,
        sessions: SessionRepository,
        passwords: PasswordManager,
        tokens: TokenManager,
        verification_tokens: VerificationTokenManager,
        password_reset_tokens: PasswordResetTokenManager,
        notifier: VerificationNotifier,
        login_limiter: LoginRateLimiter,
        audit: AuditSink,
    ) -> None:
        self._users = users
        self._sessions = sessions
        self._passwords = passwords
        self._tokens = tokens
        self._verification_tokens = verification_tokens
        self._password_reset_tokens = password_reset_tokens
        self._notifier = notifier
        self._login_limiter = login_limiter
        self._audit = audit

    async def register(self, email: str, password: str) -> User:
        if await self._users.get_by_email(email) is not None:
            raise AuthenticationError("email already registered")
        user = User(
            uuid4(),
            email,
            self._passwords.hash(password),
            Role.USER,
            True,
            False,
            datetime.now(UTC),
        )
        try:
            await self._users.add(user)
        except ValueError as error:
            raise AuthenticationError("email already registered") from error
        token = self._verification_tokens.create(user.id)
        await self._notifier.send_email_verification(user.email, token)
        await self._audit.record(event(AuditAction.USER_REGISTERED, user.id))
        return user

    async def verify_email(self, encoded_token: str) -> User:
        try:
            user_id = self._verification_tokens.decode(encoded_token)
        except InvalidTokenError as error:
            raise AuthenticationError("invalid verification token") from error
        user = await self._users.mark_verified(user_id)
        if user is None:
            raise AuthenticationError("invalid verification token")
        await self._audit.record(event(AuditAction.EMAIL_VERIFIED, user.id))
        return user

    async def request_password_reset(self, email: str) -> None:
        user = await self._users.get_by_email(email.strip().casefold())
        if user is None or not user.is_active:
            return
        token, claims = self._password_reset_tokens.create(user.id)
        await self._sessions.add(claims.token_id, user.id, claims.expires_at)
        await self._notifier.send_password_reset(user.email, token)
        await self._audit.record(event(AuditAction.PASSWORD_RESET_REQUESTED, user.id))

    async def reset_password(self, encoded_token: str, new_password: str) -> None:
        try:
            claims = self._password_reset_tokens.decode(encoded_token)
        except InvalidTokenError as error:
            raise AuthenticationError("invalid password reset token") from error
        if await self._sessions.consume(claims.token_id) != claims.user_id:
            raise AuthenticationError("invalid password reset token")
        user = await self._users.update_password(
            claims.user_id, self._passwords.hash(new_password)
        )
        if user is None:
            raise AuthenticationError("invalid password reset token")
        await self._sessions.revoke_all(user.id)
        await self._audit.record(event(AuditAction.PASSWORD_RESET_COMPLETED, user.id))

    async def login(self, email: str, password: str, attempt_key: str) -> TokenPair:
        await self._login_limiter.check(attempt_key)
        user = await self._users.get_by_email(email.strip().casefold())
        if (
            user is None
            or not user.is_active
            or not user.is_verified
            or not self._passwords.verify(password, user.password_hash)
        ):
            await self._login_limiter.record_failure(attempt_key)
            await self._audit.record(
                event(AuditAction.LOGIN_FAILED, user.id if user is not None else None)
            )
            raise AuthenticationError("invalid credentials")
        await self._login_limiter.reset(attempt_key)
        await self._audit.record(event(AuditAction.LOGIN_SUCCEEDED, user.id))
        return await self._issue_pair(user)

    async def refresh(self, encoded_token: str) -> TokenPair:
        try:
            claims = self._tokens.decode(encoded_token, "refresh")
        except InvalidTokenError as error:
            raise AuthenticationError("invalid session") from error
        if await self._sessions.consume(claims.token_id) != claims.subject:
            raise AuthenticationError("invalid session")
        user = await self._users.get_by_id(claims.subject)
        if user is None or not user.is_active:
            raise AuthenticationError("invalid session")
        await self._audit.record(event(AuditAction.TOKEN_REFRESHED, user.id))
        return await self._issue_pair(user)

    async def logout(self, encoded_token: str) -> None:
        try:
            claims = self._tokens.decode(encoded_token, "refresh")
        except InvalidTokenError:
            return
        await self._sessions.revoke(claims.token_id)
        await self._audit.record(event(AuditAction.LOGOUT, claims.subject))

    async def authenticate(self, encoded_token: str) -> User:
        try:
            claims = self._tokens.decode(encoded_token, "access")
        except InvalidTokenError as error:
            raise AuthenticationError("invalid access token") from error
        user = await self._users.get_by_id(claims.subject)
        if user is None or not user.is_active:
            raise AuthenticationError("invalid access token")
        return user

    async def list_sessions(self, user_id: UUID) -> tuple[Session, ...]:
        return await self._sessions.list_for_user(user_id)

    async def revoke_session(self, user_id: UUID, session_id: UUID) -> None:
        if not await self._sessions.revoke_for_user(session_id, user_id):
            raise AuthenticationError("session not found")
        await self._audit.record(event(AuditAction.SESSION_REVOKED, user_id))

    async def _issue_pair(self, user: User) -> TokenPair:
        access, _ = self._tokens.create(user.id, user.role, "access")
        refresh, claims = self._tokens.create(user.id, user.role, "refresh")
        await self._sessions.add(claims.token_id, user.id, claims.expires_at)
        return TokenPair(
            access_token=access,
            refresh_token=refresh,
            expires_in=self._tokens.access_ttl_seconds,
        )
