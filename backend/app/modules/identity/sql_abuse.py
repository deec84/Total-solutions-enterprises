"""Atomic PostgreSQL login limiter shared by every application replica."""

import math
from datetime import UTC, datetime, timedelta

from sqlalchemy import case, delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models import LoginRateLimitRow
from app.modules.identity.abuse import RateLimitExceeded


class SqlLoginRateLimiter:
    def __init__(
        self,
        session: AsyncSession,
        max_failures: int = 5,
        window_seconds: int = 900,
        lock_seconds: int = 900,
    ) -> None:
        if min(max_failures, window_seconds, lock_seconds) <= 0:
            raise ValueError("rate limit values must be positive")
        self._session = session
        self._max_failures = max_failures
        self._window_seconds = window_seconds
        self._lock_seconds = lock_seconds

    async def check(self, key: str) -> None:
        locked_until = await self._session.scalar(
            select(LoginRateLimitRow.locked_until).where(LoginRateLimitRow.key == key)
        )
        now = datetime.now(UTC)
        if locked_until is not None and locked_until > now:
            seconds = math.ceil((locked_until - now).total_seconds())
            raise RateLimitExceeded(max(1, seconds))
        if locked_until is not None:
            await self.reset(key)

    async def record_failure(self, key: str) -> None:
        now = datetime.now(UTC)
        cutoff = now - timedelta(seconds=self._window_seconds)
        new_lock = now + timedelta(seconds=self._lock_seconds)
        window_expired = LoginRateLimitRow.window_started_at <= cutoff
        next_count = LoginRateLimitRow.failure_count + 1
        statement = insert(LoginRateLimitRow).values(
            key=key,
            failure_count=1,
            window_started_at=now,
            locked_until=None,
            updated_at=now,
        )
        statement = statement.on_conflict_do_update(
            index_elements=[LoginRateLimitRow.key],
            set_={
                "failure_count": case((window_expired, 1), else_=next_count),
                "window_started_at": case(
                    (window_expired, now), else_=LoginRateLimitRow.window_started_at
                ),
                "locked_until": case(
                    (window_expired, None),
                    (next_count >= self._max_failures, new_lock),
                    else_=LoginRateLimitRow.locked_until,
                ),
                "updated_at": now,
            },
        )
        await self._session.execute(statement)
        retention = timedelta(seconds=max(self._window_seconds, self._lock_seconds) * 2)
        await self._session.execute(
            delete(LoginRateLimitRow).where(LoginRateLimitRow.updated_at < now - retention)
        )

    async def reset(self, key: str) -> None:
        await self._session.execute(
            delete(LoginRateLimitRow).where(LoginRateLimitRow.key == key)
        )
