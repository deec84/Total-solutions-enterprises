"""Hash-chained audit records for privileged actions."""

import hashlib
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

GENESIS_HASH = "0" * 64


@dataclass(frozen=True, slots=True)
class AdminAuditRecord:
    id: UUID
    actor_id: UUID
    action: str
    subject_id: UUID | None
    occurred_at: datetime
    previous_hash: str
    event_hash: str


def event_hash(
    actor_id: UUID,
    action: str,
    subject_id: UUID | None,
    occurred_at: datetime,
    previous_hash: str,
) -> str:
    material = "|".join(
        (str(actor_id), action, str(subject_id or ""), occurred_at.isoformat(), previous_hash)
    )
    return hashlib.sha256(material.encode()).hexdigest()


def verify_chain(records: tuple[AdminAuditRecord, ...]) -> bool:
    previous = GENESIS_HASH
    for record in records:
        if record.previous_hash != previous:
            return False
        expected = event_hash(
            record.actor_id,
            record.action,
            record.subject_id,
            record.occurred_at,
            previous,
        )
        if record.event_hash != expected:
            return False
        previous = record.event_hash
    return True
