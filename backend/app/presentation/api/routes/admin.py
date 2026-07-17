"""Separate MFA-protected administrative surface."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import database_session
from app.infrastructure.models import CommunityReportRow, SessionRow, UserRow
from app.modules.admin.schemas import (
    AdminOverview,
    AuditIntegrityResponse,
    MfaConfirmCommand,
    MfaSetupResponse,
)
from app.modules.admin.sql_audit import SqlAdminAuditTrail
from app.modules.identity.domain import Role, User
from app.modules.identity.mfa import generate_secret, provisioning_uri, verify_totp
from app.modules.identity.sql_repositories import SqlUserRepository
from app.presentation.api.routes.auth import require_roles

router = APIRouter()


async def privileged_user(
    user: Annotated[User, Depends(require_roles(Role.MODERATOR, Role.ADMIN))],
    code: Annotated[str | None, Header(alias="X-ParkShield-MFA")] = None,
) -> User:
    if not user.mfa_enabled or not user.mfa_secret:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "MFA enrollment required")
    if code is None or not verify_totp(user.mfa_secret, code):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "valid MFA code required")
    return user


@router.post("/mfa/setup", response_model=MfaSetupResponse)
async def setup_mfa(
    user: Annotated[User, Depends(require_roles(Role.MODERATOR, Role.ADMIN))],
    session: Annotated[AsyncSession, Depends(database_session)],
) -> MfaSetupResponse:
    secret = generate_secret()
    await SqlUserRepository(session).set_mfa(user.id, secret, False)
    await SqlAdminAuditTrail(session).append(user.id, "admin.mfa_setup_started", user.id)
    return MfaSetupResponse(secret=secret, provisioning_uri=provisioning_uri(secret, user.email))


@router.post("/mfa/confirm", status_code=status.HTTP_204_NO_CONTENT)
async def confirm_mfa(
    command: MfaConfirmCommand,
    user: Annotated[User, Depends(require_roles(Role.MODERATOR, Role.ADMIN))],
    session: Annotated[AsyncSession, Depends(database_session)],
) -> None:
    if not user.mfa_secret or not verify_totp(user.mfa_secret, command.code):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "invalid MFA code")
    await SqlUserRepository(session).set_mfa(user.id, user.mfa_secret, True)
    await SqlAdminAuditTrail(session).append(user.id, "admin.mfa_enabled", user.id)


@router.get("/overview", response_model=AdminOverview)
async def overview(
    _: Annotated[User, Depends(privileged_user)],
    session: Annotated[AsyncSession, Depends(database_session)],
) -> AdminOverview:
    users = await session.scalar(select(func.count()).select_from(UserRow)) or 0
    sessions = (
        await session.scalar(
            select(func.count())
            .select_from(SessionRow)
            .where(SessionRow.expires_at > datetime.now(UTC))
        )
        or 0
    )
    result = await session.execute(
        select(CommunityReportRow.status, func.count()).group_by(CommunityReportRow.status)
    )
    counts: dict[str, int] = {key: count for key, count in result.tuples()}
    return AdminOverview(
        users=users,
        active_sessions=sessions,
        pending_reports=counts.get("pending", 0),
        published_reports=counts.get("published", 0),
        rejected_reports=counts.get("rejected", 0),
    )


@router.get("/audit/integrity", response_model=AuditIntegrityResponse)
async def audit_integrity(
    _: Annotated[User, Depends(privileged_user)],
    session: Annotated[AsyncSession, Depends(database_session)],
) -> AuditIntegrityResponse:
    valid, count = await SqlAdminAuditTrail(session).verify_integrity()
    return AuditIntegrityResponse(valid=valid, records_checked=count)
