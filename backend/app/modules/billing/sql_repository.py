"""PostgreSQL adapter for subscription state and append-only billing evidence."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models import BillingEventRow, BillingSubscriptionRow
from app.modules.billing.domain import (
    BillingEvent,
    EntitlementCode,
    StoreEnvironment,
    StorePlatform,
    SubscriptionRecord,
    SubscriptionStatus,
)


def _subscription(row: BillingSubscriptionRow) -> SubscriptionRecord:
    return SubscriptionRecord(
        row.id,
        row.user_id,
        row.subject_reference,
        StorePlatform(row.platform),
        row.product_id,
        EntitlementCode(row.entitlement),
        SubscriptionStatus(row.status),
        StoreEnvironment(row.environment),
        row.transaction_reference,
        row.original_transaction_reference,
        row.purchased_at,
        row.expires_at,
        row.verified_at,
        row.auto_renews,
    )


class SqlBillingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def current(self, user_id: UUID) -> SubscriptionRecord | None:
        row = await self._session.scalar(
            select(BillingSubscriptionRow)
            .where(BillingSubscriptionRow.user_id == user_id)
            .order_by(BillingSubscriptionRow.verified_at.desc())
            .limit(1)
        )
        return _subscription(row) if row is not None else None

    async def reconcile(
        self, subscription: SubscriptionRecord, event: BillingEvent
    ) -> SubscriptionRecord:
        values = {
            "id": subscription.id,
            "user_id": subscription.user_id,
            "subject_reference": subscription.subject_reference,
            "platform": subscription.platform.value,
            "product_id": subscription.product_id,
            "entitlement": subscription.entitlement.value,
            "status": subscription.status.value,
            "environment": subscription.environment.value,
            "transaction_reference": subscription.transaction_reference,
            "original_transaction_reference": subscription.original_transaction_reference,
            "purchased_at": subscription.purchased_at,
            "expires_at": subscription.expires_at,
            "verified_at": subscription.verified_at,
            "auto_renews": subscription.auto_renews,
        }
        statement = insert(BillingSubscriptionRow).values(**values)
        await self._session.execute(
            statement.on_conflict_do_update(
                index_elements=[
                    BillingSubscriptionRow.platform,
                    BillingSubscriptionRow.environment,
                    BillingSubscriptionRow.original_transaction_reference,
                ],
                set_={key: value for key, value in values.items() if key != "id"},
                where=(
                    statement.excluded.verified_at
                    >= BillingSubscriptionRow.verified_at
                ),
            )
        )
        persisted = await self._session.scalar(
            select(BillingSubscriptionRow).where(
                BillingSubscriptionRow.platform == subscription.platform.value,
                BillingSubscriptionRow.environment == subscription.environment.value,
                BillingSubscriptionRow.original_transaction_reference
                == subscription.original_transaction_reference,
            )
        )
        if persisted is None:
            raise RuntimeError("verified subscription could not be persisted")
        event_statement = insert(BillingEventRow).values(
            id=event.id,
            subscription_id=persisted.id,
            provider_event_reference=event.provider_event_reference,
            status=event.status.value,
            occurred_at=event.occurred_at,
            received_at=event.received_at,
        )
        await self._session.execute(
            event_statement.on_conflict_do_nothing(
                index_elements=[BillingEventRow.provider_event_reference]
            )
        )
        return _subscription(persisted)
