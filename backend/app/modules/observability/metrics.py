"""Bounded local metrics provider used in development and contract tests."""

from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from threading import Lock


def _label_key(labels: Mapping[str, str] | None) -> tuple[tuple[str, str], ...]:
    if not labels:
        return ()
    return tuple(sorted((key[:32], value[:40]) for key, value in labels.items()))


@dataclass(frozen=True, slots=True)
class MetricsSnapshot:
    counters: dict[tuple[str, tuple[tuple[str, str], ...]], int]
    observations: dict[tuple[str, tuple[tuple[str, str], ...]], tuple[float, ...]]


class InMemoryMetrics:
    """Thread-safe process-local provider; no network and no persistent identifiers."""

    def __init__(self) -> None:
        self._counters: dict[tuple[str, tuple[tuple[str, str], ...]], int] = defaultdict(int)
        self._observations: dict[
            tuple[str, tuple[tuple[str, str], ...]], list[float]
        ] = defaultdict(list)
        self._lock = Lock()

    @property
    def ready(self) -> bool:
        return True

    def increment(self, name: str, labels: Mapping[str, str] | None = None) -> None:
        with self._lock:
            self._counters[(name, _label_key(labels))] += 1

    def observe(
        self, name: str, value: float, labels: Mapping[str, str] | None = None
    ) -> None:
        with self._lock:
            self._observations[(name, _label_key(labels))].append(float(value))

    def snapshot(self) -> MetricsSnapshot:
        with self._lock:
            return MetricsSnapshot(
                dict(self._counters),
                {key: tuple(values) for key, values in self._observations.items()},
            )


class DisabledMetrics:
    @property
    def ready(self) -> bool:
        return True

    def increment(self, name: str, labels: Mapping[str, str] | None = None) -> None:
        return None

    def observe(
        self, name: str, value: float, labels: Mapping[str, str] | None = None
    ) -> None:
        return None


class UnavailableMetrics(DisabledMetrics):
    """Fail readiness when a configured real exporter was not injected."""

    @property
    def ready(self) -> bool:
        return False
