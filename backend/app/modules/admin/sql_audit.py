"""Serialized PostgreSQL adapter for the administrative hash chain."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models import AdminAuditRow
from app.modules.admin.audit import GENESIS_HASH, AdminAuditRecord, event_hash, verify_chain


class SqlAdminAuditTrail:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(
        self, actor_id: UUID, action: str, subject_id: UUID | None = None
    ) -> AdminAuditRecord:
        # Transaction-level lock serializes the chain head across API replicas.
        await self._session.execute(text("SELECT pg_advisory_xact_lock(726574531)"))
        latest = await self._session.scalar(
            select(AdminAuditRow).order_by(AdminAuditRow.sequence.desc()).limit(1)
        )
        previous = latest.event_hash if latest else GENESIS_HASH
        occurred_at = datetime.now(UTC)
        digest = event_hash(actor_id, action, subject_id, occurred_at, previous)
        row = AdminAuditRow(
            id=uuid4(),
            actor_id=actor_id,
            action=action,
            subject_id=subject_id,
            occurred_at=occurred_at,
            previous_hash=previous,
            event_hash=digest,
        )
        self._session.add(row)
        await self._session.flush()
        return AdminAuditRecord(
            row.id, actor_id, action, subject_id, occurred_at, previous, digest
        )

    async def verify_integrity(self) -> tuple[bool, int]:
        rows = await self._session.scalars(
            select(AdminAuditRow).order_by(AdminAuditRow.sequence)
        )
        records = tuple(
            AdminAuditRecord(
                row.id,
                row.actor_id,
                row.action,
                row.subject_id,
                row.occurred_at,
                row.previous_hash,
                row.event_hash,
            )
            for row in rows
        )
        return verify_chain(records), len(records)
