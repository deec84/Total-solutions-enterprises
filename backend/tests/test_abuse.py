"""Deterministic authentication rate-limit tests."""

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.abuse import InMemoryLoginRateLimiter, RateLimitExceeded
from app.modules.identity.sql_abuse import SqlLoginRateLimiter


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_limiter_locks_then_expires_and_resets() -> None:
    async def scenario() -> None:
        clock = FakeClock()
        limiter = InMemoryLoginRateLimiter(
            max_failures=2, window_seconds=60, lock_seconds=30, clock=clock
        )
        await limiter.record_failure("subject")
        await limiter.check("subject")
        await limiter.record_failure("subject")
        with pytest.raises(RateLimitExceeded) as blocked:
            await limiter.check("subject")
        assert blocked.value.retry_after_seconds == 30

        clock.now += 31
        await limiter.check("subject")
        await limiter.record_failure("subject")
        await limiter.reset("subject")
        await limiter.check("subject")

    asyncio.run(scenario())


def test_limiter_rejects_invalid_configuration() -> None:
    with pytest.raises(ValueError, match="positive"):
        InMemoryLoginRateLimiter(max_failures=0)


def test_sql_limiter_checks_shared_lock_and_builds_atomic_updates() -> None:
    async def scenario() -> None:
        db = AsyncMock(spec=AsyncSession)
        limiter = SqlLoginRateLimiter(db)
        db.scalar.return_value = datetime.now(UTC) + timedelta(seconds=30)
        with pytest.raises(RateLimitExceeded):
            await limiter.check("a" * 64)

        db.scalar.return_value = datetime.now(UTC) - timedelta(seconds=1)
        await limiter.check("a" * 64)
        await limiter.record_failure("a" * 64)
        await limiter.reset("a" * 64)
        assert db.execute.await_count == 4

    asyncio.run(scenario())


def test_sql_limiter_rejects_invalid_configuration() -> None:
    with pytest.raises(ValueError, match="positive"):
        SqlLoginRateLimiter(AsyncMock(spec=AsyncSession), max_failures=0)
