"""Authentication HTTP adapter."""

import hashlib
from collections.abc import Awaitable, Callable
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import database_session
from app.modules.identity.abuse import InMemoryLoginRateLimiter, RateLimitExceeded
from app.modules.identity.audit import AuditSink, InMemoryAuditSink
from app.modules.identity.authorization import AuthorizationError, authorize
from app.modules.identity.domain import Role, User, VerificationNotifier
from app.modules.identity.notifications import SmtpVerificationNotifier
from app.modules.identity.repositories import (
    InMemorySessionRepository,
    InMemoryUserRepository,
    InMemoryVerificationNotifier,
)
from app.modules.identity.schemas import (
    LoginCommand,
    LogoutCommand,
    MessageResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshCommand,
    RegisterCommand,
    SessionResponse,
    TokenPair,
    UserResponse,
    VerifyEmailCommand,
)
from app.modules.identity.security import (
    PasswordManager,
    PasswordResetTokenManager,
    TokenManager,
    VerificationTokenManager,
)
from app.modules.identity.service import AuthenticationError, IdentityService
from app.modules.identity.sql_abuse import SqlLoginRateLimiter
from app.modules.identity.sql_repositories import (
    SqlAuditSink,
    SqlSessionRepository,
    SqlUserRepository,
)
from app.shared.config import get_settings

router = APIRouter()
bearer = HTTPBearer(auto_error=False)


def build_identity_service(
    notifier: VerificationNotifier | None = None, audit: AuditSink | None = None
) -> IdentityService:
    settings = get_settings()
    resolved_notifier = notifier or build_verification_notifier()
    return IdentityService(
        InMemoryUserRepository(),
        InMemorySessionRepository(),
        PasswordManager(),
        TokenManager(
            settings.jwt_secret,
            settings.access_token_ttl_minutes,
            settings.refresh_token_ttl_days,
        ),
        VerificationTokenManager(settings.jwt_secret),
        PasswordResetTokenManager(settings.jwt_secret),
        resolved_notifier,
        InMemoryLoginRateLimiter(),
        audit or InMemoryAuditSink(),
    )


def build_verification_notifier() -> VerificationNotifier:
    settings = get_settings()
    if settings.environment in {"staging", "production"}:
        host = settings.smtp_host
        username = settings.smtp_username
        password = settings.smtp_password
        if not host or not username or not password:
            raise RuntimeError("SMTP configuration is required outside local/test environments")
        return SmtpVerificationNotifier(
            host=host,
            port=settings.smtp_port,
            username=username,
            password=password,
            sender=settings.email_from,
            link_scheme=settings.mobile_link_scheme,
        )
    return InMemoryVerificationNotifier()


_verification_notifier = build_verification_notifier()


def get_identity_service(
    session: Annotated[AsyncSession, Depends(database_session)],
) -> IdentityService:
    settings = get_settings()
    return IdentityService(
        SqlUserRepository(session),
        SqlSessionRepository(session),
        PasswordManager(),
        TokenManager(
            settings.jwt_secret,
            settings.access_token_ttl_minutes,
            settings.refresh_token_ttl_days,
        ),
        VerificationTokenManager(settings.jwt_secret),
        PasswordResetTokenManager(settings.jwt_secret),
        _verification_notifier,
        SqlLoginRateLimiter(session),
        SqlAuditSink(session),
    )


def user_response(user: User) -> UserResponse:
    return UserResponse(
        id=str(user.id), email=user.email, role=user.role, is_verified=user.is_verified
    )


async def current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    service: Annotated[IdentityService, Depends(get_identity_service)],
) -> User:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "authentication required")
    try:
        return await service.authenticate(credentials.credentials)
    except AuthenticationError as error:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(error)) from error


def require_roles(*allowed_roles: Role) -> Callable[..., Awaitable[User]]:
    """Build a deny-by-default FastAPI dependency for privileged endpoints."""

    async def dependency(user: Annotated[User, Depends(current_user)]) -> User:
        try:
            authorize(user, set(allowed_roles))
        except AuthorizationError as error:
            raise HTTPException(status.HTTP_403_FORBIDDEN, str(error)) from error
        return user

    return dependency


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    command: RegisterCommand,
    service: Annotated[IdentityService, Depends(get_identity_service)],
) -> UserResponse:
    try:
        return user_response(await service.register(command.email, command.password))
    except AuthenticationError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error


@router.post("/login", response_model=TokenPair)
async def login(
    command: LoginCommand,
    request: Request,
    service: Annotated[IdentityService, Depends(get_identity_service)],
) -> TokenPair:
    client_host = request.client.host if request.client is not None else "unknown"
    attempt_key = hashlib.sha256(
        f"{client_host}:{command.email.strip().casefold()}".encode()
    ).hexdigest()
    try:
        return await service.login(command.email, command.password, attempt_key)
    except RateLimitExceeded as error:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "too many authentication attempts",
            headers={"Retry-After": str(error.retry_after_seconds)},
        ) from error
    except AuthenticationError as error:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(error)) from error


@router.post("/verify-email", response_model=UserResponse)
async def verify_email(
    command: VerifyEmailCommand,
    service: Annotated[IdentityService, Depends(get_identity_service)],
) -> UserResponse:
    try:
        return user_response(await service.verify_email(command.token))
    except AuthenticationError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    command: RefreshCommand,
    service: Annotated[IdentityService, Depends(get_identity_service)],
) -> TokenPair:
    try:
        return await service.refresh(command.refresh_token)
    except AuthenticationError as error:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(error)) from error


@router.post("/password-reset/request", response_model=MessageResponse)
async def request_password_reset(
    command: PasswordResetRequest,
    service: Annotated[IdentityService, Depends(get_identity_service)],
) -> MessageResponse:
    await service.request_password_reset(command.email)
    return MessageResponse(message="If the account exists, reset instructions were sent.")


@router.post("/password-reset/confirm", response_model=MessageResponse)
async def confirm_password_reset(
    command: PasswordResetConfirm,
    service: Annotated[IdentityService, Depends(get_identity_service)],
) -> MessageResponse:
    try:
        await service.reset_password(command.token, command.new_password)
    except AuthenticationError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error
    return MessageResponse(message="Password updated.")


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    command: LogoutCommand,
    service: Annotated[IdentityService, Depends(get_identity_service)],
) -> None:
    await service.logout(command.refresh_token)


@router.get("/me", response_model=UserResponse)
async def me(user: Annotated[User, Depends(current_user)]) -> UserResponse:
    return user_response(user)


@router.get("/sessions", response_model=list[SessionResponse])
async def sessions(
    user: Annotated[User, Depends(current_user)],
    service: Annotated[IdentityService, Depends(get_identity_service)],
) -> list[SessionResponse]:
    active = await service.list_sessions(user.id)
    return [
        SessionResponse(
            id=str(session.id),
            created_at=session.created_at.isoformat(),
            expires_at=session.expires_at.isoformat(),
        )
        for session in active
    ]


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_session(
    session_id: UUID,
    user: Annotated[User, Depends(current_user)],
    service: Annotated[IdentityService, Depends(get_identity_service)],
) -> None:
    try:
        await service.revoke_session(user.id, session_id)
    except AuthenticationError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
