"""Local Tesseract OCR adapter; image bytes never leave the service."""

from typing import Any

import pytesseract  # type: ignore[import-untyped]
from PIL import Image
from pytesseract import Output

from app.modules.sign_scanner.domain import OcrResult


class TesseractOcrProvider:
    def extract(self, image: Image.Image) -> OcrResult:
        data: dict[str, list[Any]] = pytesseract.image_to_data(
            image,
            lang="eng+spa",
            config="--psm 6",
            output_type=Output.DICT,
        )
        words: list[str] = []
        confidences: list[float] = []
        for text, raw_confidence in zip(data["text"], data["conf"], strict=True):
            cleaned = str(text).strip()
            confidence = float(raw_confidence)
            if cleaned and confidence >= 0:
                words.append(cleaned)
                confidences.append(confidence / 100)
        combined = " ".join(words)
        average = sum(confidences) / len(confidences) if confidences else 0.0
        language = "es" if _looks_spanish(combined) else "en"
        return OcrResult(combined, average, language, "tesseract-5-eng-spa")


def _looks_spanish(text: str) -> bool:
    normalized = text.casefold()
    return any(word in normalized for word in ("estacionar", "remolque", "permiso", "excepto"))
