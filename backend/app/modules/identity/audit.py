"""Security audit events and an adapter boundary for immutable persistence."""

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID


class AuditAction(StrEnum):
    USER_REGISTERED = "user.registered"
    EMAIL_VERIFIED = "user.email_verified"
    LOGIN_SUCCEEDED = "session.login_succeeded"
    LOGIN_FAILED = "session.login_failed"
    TOKEN_REFRESHED = "session.token_refreshed"
    LOGOUT = "session.logout"
    SESSION_REVOKED = "session.revoked"
    PASSWORD_RESET_REQUESTED = "user.password_reset_requested"
    PASSWORD_RESET_COMPLETED = "user.password_reset_completed"


@dataclass(frozen=True, slots=True)
class AuditEvent:
    action: AuditAction
    subject_id: UUID | None
    occurred_at: datetime


class AuditSink(Protocol):
    async def record(self, event: AuditEvent) -> None: ...


class InMemoryAuditSink:
    def __init__(self) -> None:
        self._events: list[AuditEvent] = []
        self._lock = asyncio.Lock()

    async def record(self, event: AuditEvent) -> None:
        async with self._lock:
            self._events.append(event)

    def events(self) -> tuple[AuditEvent, ...]:
        return tuple(self._events)


def event(action: AuditAction, subject_id: UUID | None = None) -> AuditEvent:
    return AuditEvent(action, subject_id, datetime.now(UTC))
