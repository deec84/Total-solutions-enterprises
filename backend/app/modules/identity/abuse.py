"""Authentication abuse controls with a replaceable distributed adapter boundary."""

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class RateLimitExceeded(PermissionError):
    retry_after_seconds: int


@dataclass(slots=True)
class AttemptState:
    failures: list[float]
    locked_until: float | None = None


class LoginRateLimiter(Protocol):
    async def check(self, key: str) -> None: ...
    async def record_failure(self, key: str) -> None: ...
    async def reset(self, key: str) -> None: ...


class InMemoryLoginRateLimiter:
    """Sliding-window adapter for isolated tests and single-process development."""

    def __init__(
        self,
        max_failures: int = 5,
        window_seconds: int = 900,
        lock_seconds: int = 900,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if min(max_failures, window_seconds, lock_seconds) <= 0:
            raise ValueError("rate limit values must be positive")
        self._max_failures = max_failures
        self._window_seconds = window_seconds
        self._lock_seconds = lock_seconds
        self._clock = clock
        self._states: dict[str, AttemptState] = {}
        self._lock = asyncio.Lock()

    async def check(self, key: str) -> None:
        async with self._lock:
            now = self._clock()
            state = self._states.get(key)
            if state is None:
                return
            if state.locked_until is not None and state.locked_until > now:
                raise RateLimitExceeded(max(1, int(state.locked_until - now)))
            if state.locked_until is not None:
                self._states.pop(key, None)

    async def record_failure(self, key: str) -> None:
        async with self._lock:
            now = self._clock()
            state = self._states.setdefault(key, AttemptState([]))
            state.failures = [
                timestamp
                for timestamp in state.failures
                if timestamp > now - self._window_seconds
            ]
            state.failures.append(now)
            if len(state.failures) >= self._max_failures:
                state.locked_until = now + self._lock_seconds

    async def reset(self, key: str) -> None:
        async with self._lock:
            self._states.pop(key, None)
