from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID


class DevicePlatform(StrEnum):
    ANDROID = "android"
    IOS = "ios"


@dataclass(frozen=True, slots=True)
class NotificationPreferences:
    user_id: UUID
    parking_alerts_enabled: bool
    background_location_enabled: bool
    push_enabled: bool
    quiet_start_hour: int
    quiet_end_hour: int
    timezone: str
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class PushDevice:
    id: UUID
    user_id: UUID
    platform: DevicePlatform
    token: str
    enabled: bool
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class AlertDecision:
    should_alert: bool
    reason: str
    parking_score: int | None
    risk_level: str | None
    estimated_towing_cost_cents: int | None
    deduplicated: bool = False


class NotificationRepository(Protocol):
    async def preferences(self, user_id: UUID) -> NotificationPreferences: ...
    async def save_preferences(
        self, preferences: NotificationPreferences
    ) -> NotificationPreferences: ...
    async def register_device(self, device: PushDevice) -> PushDevice: ...
    async def devices(self, user_id: UUID) -> tuple[PushDevice, ...]: ...
    async def claim_delivery(self, user_id: UUID, dedupe_key: str, now: datetime) -> bool: ...
    async def record_delivery(self, user_id: UUID, status: str, now: datetime) -> None: ...


class PushProvider(Protocol):
    async def send(
        self, device: PushDevice, title: str, body: str, data: dict[str, str]
    ) -> bool: ...
