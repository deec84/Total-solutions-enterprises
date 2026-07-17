from datetime import UTC, datetime
from uuid import UUID

from app.modules.notifications.domain import NotificationPreferences, PushDevice


class InMemoryNotificationRepository:
    def __init__(self) -> None:
        self._preferences: dict[UUID, NotificationPreferences] = {}
        self._devices: dict[UUID, PushDevice] = {}
        self._dedupe: set[tuple[UUID, str]] = set()
        self.deliveries: list[tuple[UUID, str, datetime]] = []

    async def preferences(self, user_id: UUID) -> NotificationPreferences:
        return self._preferences.get(
            user_id,
            NotificationPreferences(user_id, False, False, False, 22, 7, "UTC", datetime.now(UTC)),
        )

    async def save_preferences(
        self, preferences: NotificationPreferences
    ) -> NotificationPreferences:
        self._preferences[preferences.user_id] = preferences
        return preferences

    async def register_device(self, device: PushDevice) -> PushDevice:
        self._devices[device.id] = device
        return device

    async def devices(self, user_id: UUID) -> tuple[PushDevice, ...]:
        return tuple(
            device
            for device in self._devices.values()
            if device.user_id == user_id and device.enabled
        )

    async def claim_delivery(self, user_id: UUID, dedupe_key: str, now: datetime) -> bool:
        key = (user_id, dedupe_key)
        if key in self._dedupe:
            return False
        self._dedupe.add(key)
        return True

    async def record_delivery(self, user_id: UUID, status: str, now: datetime) -> None:
        self.deliveries.append((user_id, status, now))


class InMemoryPushProvider:
    def __init__(self, succeeds: bool = True) -> None:
        self.succeeds = succeeds
        self.messages: list[tuple[PushDevice, str, str, dict[str, str]]] = []

    async def send(
        self, device: PushDevice, title: str, body: str, data: dict[str, str]
    ) -> bool:
        self.messages.append((device, title, body, data))
        return self.succeeds
