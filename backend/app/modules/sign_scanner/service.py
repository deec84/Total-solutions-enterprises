"""Secure in-memory sign scanning pipeline."""

import re
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

from app.modules.sign_scanner.domain import OcrProvider, SignScanResult
from app.modules.sign_scanner.interpreter import SignInterpreter

MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 24_000_000


class InvalidSignImageError(ValueError):
    pass


class SignScannerService:
    def __init__(self, ocr: OcrProvider, interpreter: SignInterpreter) -> None:
        self._ocr = ocr
        self._interpreter = interpreter

    def scan(self, content: bytes) -> SignScanResult:
        if not content or len(content) > MAX_IMAGE_BYTES:
            raise InvalidSignImageError("image must be between 1 byte and 10 MB")
        image = self._decode(content)
        ocr = self._ocr.extract(image)
        redacted = _redact_pii(ocr.text)
        summary, restrictions, towing_risk = self._interpreter.interpret(redacted)
        confidence = min(max(ocr.confidence, 0), 1)
        return SignScanResult(
            detected_text=ocr.text,
            redacted_text=redacted,
            language=ocr.language,
            summary=summary,
            restrictions=restrictions,
            towing_risk_score=towing_risk,
            confidence=confidence,
            requires_human_review=(confidence < 0.75 or not restrictions),
            provider_version=ocr.provider_version,
        )

    def _decode(self, content: bytes) -> Image.Image:
        try:
            with Image.open(BytesIO(content)) as candidate:
                candidate.verify()
            with Image.open(BytesIO(content)) as candidate:
                width, height = candidate.size
                if width * height > MAX_IMAGE_PIXELS:
                    raise InvalidSignImageError("decoded image is too large")
                return ImageOps.exif_transpose(candidate).convert("RGB")
        except (UnidentifiedImageError, OSError) as error:
            raise InvalidSignImageError("unsupported or corrupt image") from error


def _redact_pii(text: str) -> str:
    redacted = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[EMAIL REDACTED]", text)
    return re.sub(
        r"(?<!\d)(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}(?!\d)",
        "[PHONE REDACTED]",
        redacted,
    )
