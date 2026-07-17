import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from app.infrastructure.models import AdminAuditRow
from app.modules.admin.audit import GENESIS_HASH, AdminAuditRecord, event_hash, verify_chain
from app.modules.admin.sql_audit import SqlAdminAuditTrail


def test_admin_audit_chain_detects_modified_or_removed_events() -> None:
    actor = uuid4()
    first_time = datetime.now(UTC)
    first_hash = event_hash(actor, "report.approved", uuid4(), first_time, GENESIS_HASH)
    first = AdminAuditRecord(
        uuid4(), actor, "report.approved", None, first_time, GENESIS_HASH, first_hash
    )
    # Rebuild with the same subject used by the hash.
    subject = uuid4()
    first_hash = event_hash(actor, "report.approved", subject, first_time, GENESIS_HASH)
    first = AdminAuditRecord(
        first.id, actor, "report.approved", subject, first_time, GENESIS_HASH, first_hash
    )
    second_time = first_time + timedelta(seconds=1)
    second_hash = event_hash(actor, "appeal.overturned", subject, second_time, first_hash)
    second = AdminAuditRecord(
        uuid4(), actor, "appeal.overturned", subject, second_time, first_hash, second_hash
    )

    assert verify_chain((first, second))
    assert not verify_chain((second,))
    tampered = AdminAuditRecord(
        second.id,
        second.actor_id,
        "appeal.upheld",
        second.subject_id,
        second.occurred_at,
        second.previous_hash,
        second.event_hash,
    )
    assert not verify_chain((first, tampered))


def test_sql_audit_starts_with_genesis_and_serializes_writer() -> None:
    async def scenario() -> None:
        session = AsyncMock()
        session.scalar.return_value = None
        session.add = Mock()
        actor = uuid4()
        record = await SqlAdminAuditTrail(session).append(actor, "admin.test")
        assert record.previous_hash == GENESIS_HASH
        assert verify_chain((record,))
        session.execute.assert_awaited_once()
        session.add.assert_called_once()
        session.flush.assert_awaited_once()

    asyncio.run(scenario())


def test_sql_audit_integrity_handles_empty_chain() -> None:
    async def scenario() -> None:
        session = AsyncMock()
        session.scalars.return_value = ()
        valid, count = await SqlAdminAuditTrail(session).verify_integrity()
        assert valid
        assert count == 0

    asyncio.run(scenario())


def test_admin_audit_sequence_uses_database_identity() -> None:
    sequence = AdminAuditRow.__table__.c.sequence
    assert sequence.identity is not None
    assert sequence.unique
    assert not sequence.nullable
