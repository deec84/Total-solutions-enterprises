"""In-memory privacy adapter for isolated service and API tests."""

import asyncio
from dataclasses import replace
from datetime import datetime
from uuid import UUID

from app.modules.privacy.domain import (
    ConsentDecision,
    DataRequestStatus,
    DataRightsRequest,
)


class InMemoryPrivacyRepository:
    def __init__(
        self,
        export_data: dict[str, object] | None = None,
        media_keys: tuple[str, ...] = (),
    ) -> None:
        self._consents: list[ConsentDecision] = []
        self._requests: dict[UUID, DataRightsRequest] = {}
        self._export_data = export_data or {"profile": {}}
        self._media_keys = media_keys
        self._deleted_users: set[UUID] = set()
        self._lock = asyncio.Lock()

    async def record_consent(self, decision: ConsentDecision) -> None:
        async with self._lock:
            self._consents.append(decision)

    async def latest_consents(self, user_id: UUID) -> tuple[ConsentDecision, ...]:
        latest: dict[object, ConsentDecision] = {}
        async with self._lock:
            for item in sorted(self._consents, key=lambda value: value.occurred_at):
                if item.user_id == user_id:
                    latest[item.purpose] = item
        return tuple(sorted(latest.values(), key=lambda value: value.purpose.value))

    async def add_request(self, request: DataRightsRequest) -> None:
        async with self._lock:
            self._requests[request.id] = request

    async def complete_request(self, request_id: UUID, completed_at: datetime) -> None:
        async with self._lock:
            request = self._requests[request_id]
            self._requests[request_id] = replace(
                request, status=DataRequestStatus.COMPLETED, completed_at=completed_at
            )

    async def export_for_user(self, user_id: UUID) -> dict[str, object]:
        return self._export_data

    async def active_media_keys(self, user_id: UUID) -> tuple[str, ...]:
        return self._media_keys

    async def delete_account(self, user_id: UUID) -> bool:
        async with self._lock:
            self._deleted_users.add(user_id)
        return True

    def request(self, request_id: UUID) -> DataRightsRequest:
        return self._requests[request_id]

    def deleted(self, user_id: UUID) -> bool:
        return user_id in self._deleted_users
