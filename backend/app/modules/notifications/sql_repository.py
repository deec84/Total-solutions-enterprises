import hashlib
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models import (
    AlertDeliveryRow,
    NotificationPreferenceRow,
    PushDeviceRow,
)
from app.modules.identity.mfa import decrypt_secret, encrypt_secret
from app.modules.notifications.domain import (
    DevicePlatform,
    NotificationPreferences,
    PushDevice,
)
from app.shared.config import get_settings


class SqlNotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def preferences(self, user_id: UUID) -> NotificationPreferences:
        row = await self._session.get(NotificationPreferenceRow, user_id)
        if row is None:
            return NotificationPreferences(
                user_id, False, False, False, 22, 7, "UTC", datetime.now(UTC)
            )
        return NotificationPreferences(
            row.user_id,
            row.parking_alerts_enabled,
            row.background_location_enabled,
            row.push_enabled,
            row.quiet_start_hour,
            row.quiet_end_hour,
            row.timezone,
            row.updated_at,
        )

    async def save_preferences(
        self, preferences: NotificationPreferences
    ) -> NotificationPreferences:
        statement = insert(NotificationPreferenceRow).values(
            user_id=preferences.user_id,
            parking_alerts_enabled=preferences.parking_alerts_enabled,
            background_location_enabled=preferences.background_location_enabled,
            push_enabled=preferences.push_enabled,
            quiet_start_hour=preferences.quiet_start_hour,
            quiet_end_hour=preferences.quiet_end_hour,
            timezone=preferences.timezone,
            updated_at=preferences.updated_at,
        )
        await self._session.execute(
            statement.on_conflict_do_update(
                index_elements=[NotificationPreferenceRow.user_id],
                set_={
                    "parking_alerts_enabled": preferences.parking_alerts_enabled,
                    "background_location_enabled": preferences.background_location_enabled,
                    "push_enabled": preferences.push_enabled,
                    "quiet_start_hour": preferences.quiet_start_hour,
                    "quiet_end_hour": preferences.quiet_end_hour,
                    "timezone": preferences.timezone,
                    "updated_at": preferences.updated_at,
                },
            )
        )
        return preferences

    async def register_device(self, device: PushDevice) -> PushDevice:
        digest = hashlib.sha256(device.token.encode()).hexdigest()
        ciphertext = encrypt_secret(device.token, get_settings().jwt_secret)
        statement = insert(PushDeviceRow).values(
            id=device.id,
            user_id=device.user_id,
            platform=device.platform,
            token_ciphertext=ciphertext,
            token_hash=digest,
            enabled=device.enabled,
            updated_at=device.updated_at,
        )
        await self._session.execute(
            statement.on_conflict_do_update(
                index_elements=[PushDeviceRow.token_hash],
                set_={
                    "user_id": device.user_id,
                    "platform": device.platform,
                    "token_ciphertext": ciphertext,
                    "enabled": True,
                    "updated_at": device.updated_at,
                },
            )
        )
        return device

    async def devices(self, user_id: UUID) -> tuple[PushDevice, ...]:
        rows = await self._session.scalars(
            select(PushDeviceRow).where(
                PushDeviceRow.user_id == user_id, PushDeviceRow.enabled.is_(True)
            )
        )
        return tuple(
            PushDevice(
                row.id,
                row.user_id,
                DevicePlatform(row.platform),
                decrypt_secret(row.token_ciphertext, get_settings().jwt_secret),
                row.enabled,
                row.updated_at,
            )
            for row in rows
        )

    async def claim_delivery(self, user_id: UUID, dedupe_key: str, now: datetime) -> bool:
        result = await self._session.execute(
            insert(AlertDeliveryRow)
            .values(
                id=uuid4(),
                user_id=user_id,
                dedupe_key=dedupe_key,
                status="claimed",
                created_at=now,
            )
            .on_conflict_do_nothing(
                index_elements=[AlertDeliveryRow.user_id, AlertDeliveryRow.dedupe_key]
            )
            .returning(AlertDeliveryRow.id)
        )
        return result.scalar_one_or_none() is not None

    async def record_delivery(self, user_id: UUID, status: str, now: datetime) -> None:
        self._session.add(
            AlertDeliveryRow(
                id=uuid4(), user_id=user_id, status=status, dedupe_key=None, created_at=now
            )
        )
