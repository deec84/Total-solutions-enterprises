import hashlib
from datetime import UTC, datetime
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.modules.notifications.domain import (
    AlertDecision,
    DevicePlatform,
    NotificationPreferences,
    NotificationRepository,
    PushDevice,
    PushProvider,
)
from app.modules.parking.service import ParkingMapService


class InvalidNotificationPreference(ValueError):
    pass


class NotificationService:
    def __init__(
        self,
        repository: NotificationRepository,
        push_provider: PushProvider,
        parking: ParkingMapService,
    ) -> None:
        self._repository = repository
        self._push = push_provider
        self._parking = parking

    async def update_preferences(
        self,
        user_id: UUID,
        *,
        parking_alerts_enabled: bool,
        background_location_enabled: bool,
        push_enabled: bool,
        quiet_start_hour: int,
        quiet_end_hour: int,
        timezone: str,
    ) -> NotificationPreferences:
        if background_location_enabled and not parking_alerts_enabled:
            raise InvalidNotificationPreference("background location requires parking alerts")
        if not 0 <= quiet_start_hour <= 23 or not 0 <= quiet_end_hour <= 23:
            raise InvalidNotificationPreference("quiet hours must be between 0 and 23")
        try:
            ZoneInfo(timezone)
        except ZoneInfoNotFoundError as error:
            raise InvalidNotificationPreference("unknown timezone") from error
        return await self._repository.save_preferences(
            NotificationPreferences(
                user_id,
                parking_alerts_enabled,
                background_location_enabled,
                push_enabled,
                quiet_start_hour,
                quiet_end_hour,
                timezone,
                datetime.now(UTC),
            )
        )

    async def register_device(
        self, user_id: UUID, platform: DevicePlatform, token: str
    ) -> PushDevice:
        if len(token.strip()) < 20 or len(token) > 4096:
            raise InvalidNotificationPreference("invalid device token")
        return await self._repository.register_device(
            PushDevice(uuid4(), user_id, platform, token.strip(), True, datetime.now(UTC))
        )

    async def evaluate_location(
        self, user_id: UUID, latitude: float, longitude: float, now: datetime | None = None
    ) -> AlertDecision:
        moment = now or datetime.now(UTC)
        preferences = await self._repository.preferences(user_id)
        if not preferences.parking_alerts_enabled:
            return AlertDecision(False, "Parking alerts are disabled.", None, None, None)
        if not preferences.background_location_enabled:
            return AlertDecision(
                False, "Background location consent is disabled.", None, None, None
            )
        zone = await self._parking.decision(longitude, latitude)
        if zone is None:
            return AlertDecision(
                False,
                "No verified parking intelligence covers this location.",
                None,
                None,
                None,
            )
        if zone.parking_score >= 60:
            return AlertDecision(
                False,
                "No preventive warning is required.",
                zone.parking_score,
                zone.risk_level,
                zone.average_towing_cost_cents,
            )
        if self._is_quiet(preferences, moment):
            return AlertDecision(
                False,
                "Suppressed by quiet hours.",
                zone.parking_score,
                zone.risk_level,
                zone.average_towing_cost_cents,
            )
        dedupe_key = hashlib.sha256(
            f"{latitude:.4f}:{longitude:.4f}:{zone.risk_level}:{moment:%Y%m%d%H}".encode()
        ).hexdigest()
        if not await self._repository.claim_delivery(user_id, dedupe_key, moment):
            return AlertDecision(
                False,
                "A matching alert was already delivered.",
                zone.parking_score,
                zone.risk_level,
                zone.average_towing_cost_cents,
                True,
            )
        decision = AlertDecision(
            True,
            zone.restriction_summary or "High parking or towing risk detected.",
            zone.parking_score,
            zone.risk_level,
            zone.average_towing_cost_cents,
        )
        if preferences.push_enabled:
            devices = await self._repository.devices(user_id)
            outcomes = [
                await self._push.send(
                    device,
                    "Parking risk warning",
                    decision.reason,
                    {"parking_score": str(zone.parking_score), "risk_level": zone.risk_level},
                )
                for device in devices
            ]
            await self._repository.record_delivery(
                user_id, "delivered" if any(outcomes) else "failed", moment
            )
        return decision

    @staticmethod
    def _is_quiet(preferences: NotificationPreferences, moment: datetime) -> bool:
        hour = moment.astimezone(ZoneInfo(preferences.timezone)).hour
        start, end = preferences.quiet_start_hour, preferences.quiet_end_hour
        if start == end:
            return False
        return start <= hour < end if start < end else hour >= start or hour < end
