"""Sign-scanner contracts."""

from dataclasses import dataclass
from typing import Protocol

from PIL import Image


@dataclass(frozen=True, slots=True)
class OcrResult:
    text: str
    confidence: float
    language: str
    provider_version: str


class OcrProvider(Protocol):
    def extract(self, image: Image.Image) -> OcrResult: ...


@dataclass(frozen=True, slots=True)
class SignScanResult:
    detected_text: str
    redacted_text: str
    language: str
    summary: str
    restrictions: tuple[str, ...]
    towing_risk_score: int
    confidence: float
    requires_human_review: bool
    provider_version: str
