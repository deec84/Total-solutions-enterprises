"""PostgreSQL implementations of identity repository and audit ports."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models import AuditEventRow, SessionRow, UserRow
from app.modules.identity.audit import AuditEvent, AuditSink
from app.modules.identity.domain import Role, Session, SessionRepository, User, UserRepository
from app.modules.identity.mfa import decrypt_secret, encrypt_secret
from app.shared.config import get_settings


def _user(row: UserRow) -> User:
    return User(
        id=row.id,
        email=row.email,
        password_hash=row.password_hash,
        role=Role(row.role),
        is_active=row.is_active,
        is_verified=row.is_verified,
        created_at=row.created_at,
        mfa_secret=(
            decrypt_secret(row.mfa_secret, get_settings().jwt_secret) if row.mfa_secret else None
        ),
        mfa_enabled=row.mfa_enabled,
    )


def _session(row: SessionRow) -> Session:
    return Session(row.id, row.user_id, row.created_at, row.expires_at)


class SqlUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, user: User) -> None:
        self._session.add(
            UserRow(
                id=user.id,
                email=user.email,
                password_hash=user.password_hash,
                role=user.role.value,
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=user.created_at,
                mfa_secret=(
                    encrypt_secret(user.mfa_secret, get_settings().jwt_secret)
                    if user.mfa_secret
                    else None
                ),
                mfa_enabled=user.mfa_enabled,
            )
        )
        try:
            await self._session.flush()
        except IntegrityError as error:
            raise ValueError("email already registered") from error

    async def get_by_email(self, email: str) -> User | None:
        row = await self._session.scalar(select(UserRow).where(UserRow.email == email))
        return _user(row) if row is not None else None

    async def get_by_id(self, user_id: UUID) -> User | None:
        row = await self._session.get(UserRow, user_id)
        return _user(row) if row is not None else None

    async def mark_verified(self, user_id: UUID) -> User | None:
        result = await self._session.execute(
            update(UserRow)
            .where(UserRow.id == user_id)
            .values(is_verified=True)
            .returning(UserRow)
        )
        row = result.scalar_one_or_none()
        return _user(row) if row is not None else None

    async def update_password(self, user_id: UUID, password_hash: str) -> User | None:
        result = await self._session.execute(
            update(UserRow)
            .where(UserRow.id == user_id)
            .values(password_hash=password_hash)
            .returning(UserRow)
        )
        row = result.scalar_one_or_none()
        return _user(row) if row is not None else None

    async def set_mfa(self, user_id: UUID, secret: str, enabled: bool) -> User | None:
        result = await self._session.execute(
            update(UserRow)
            .where(UserRow.id == user_id)
            .values(
                mfa_secret=encrypt_secret(secret, get_settings().jwt_secret),
                mfa_enabled=enabled,
            )
            .returning(UserRow)
        )
        row = result.scalar_one_or_none()
        return _user(row) if row is not None else None


class SqlSessionRepository(SessionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, token_id: UUID, user_id: UUID, expires_at: datetime) -> None:
        self._session.add(
            SessionRow(
                id=token_id,
                user_id=user_id,
                created_at=datetime.now(UTC),
                expires_at=expires_at,
            )
        )
        await self._session.flush()

    async def consume(self, token_id: UUID) -> UUID | None:
        result = await self._session.execute(
            delete(SessionRow)
            .where(SessionRow.id == token_id, SessionRow.expires_at > datetime.now(UTC))
            .returning(SessionRow.user_id)
        )
        return result.scalar_one_or_none()

    async def revoke(self, token_id: UUID) -> None:
        await self._session.execute(delete(SessionRow).where(SessionRow.id == token_id))

    async def revoke_all(self, user_id: UUID) -> None:
        await self._session.execute(delete(SessionRow).where(SessionRow.user_id == user_id))

    async def list_for_user(self, user_id: UUID) -> tuple[Session, ...]:
        rows = await self._session.scalars(
            select(SessionRow)
            .where(
                SessionRow.user_id == user_id,
                SessionRow.expires_at > datetime.now(UTC),
            )
            .order_by(SessionRow.created_at)
        )
        return tuple(_session(row) for row in rows)

    async def revoke_for_user(self, token_id: UUID, user_id: UUID) -> bool:
        result = await self._session.execute(
            delete(SessionRow)
            .where(SessionRow.id == token_id, SessionRow.user_id == user_id)
            .returning(SessionRow.id)
        )
        return result.scalar_one_or_none() is not None


class SqlAuditSink(AuditSink):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(self, event: AuditEvent) -> None:
        self._session.add(
            AuditEventRow(
                id=uuid4(),
                action=event.action.value,
                subject_id=event.subject_id,
                occurred_at=event.occurred_at,
            )
        )
        await self._session.flush()
