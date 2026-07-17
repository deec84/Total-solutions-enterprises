"""Image safety, privacy redaction, interpretation, and scanner API tests."""

from datetime import UTC, datetime
from io import BytesIO
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import create_app
from app.modules.identity.domain import Role, User
from app.modules.sign_scanner.domain import OcrResult
from app.modules.sign_scanner.interpreter import SignInterpreter
from app.modules.sign_scanner.service import InvalidSignImageError, SignScannerService
from app.presentation.api.routes.auth import current_user
from app.presentation.api.routes.sign_scanner import sign_scanner_service


class FakeOcr:
    def __init__(self, text: str, confidence: float = 0.95, language: str = "en") -> None:
        self.result = OcrResult(text, confidence, language, "fake-ocr-1")

    def extract(self, image: Image.Image) -> OcrResult:
        assert image.mode == "RGB"
        return self.result


def png() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (100, 80), "white").save(buffer, format="PNG")
    return buffer.getvalue()


def test_scanner_redacts_pii_and_extracts_high_risk_restrictions() -> None:
    scanner = SignScannerService(
        FakeOcr("NO PARKING TOW AWAY call 305-555-1212"), SignInterpreter()
    )
    result = scanner.scan(png())
    assert "305-555-1212" not in result.redacted_text
    assert "[PHONE REDACTED]" in result.redacted_text
    assert result.towing_risk_score == 100
    assert "Parking is prohibited." in result.restrictions
    assert result.requires_human_review is False


def test_low_confidence_unknown_sign_requires_review() -> None:
    result = SignScannerService(FakeOcr("WELCOME", 0.4), SignInterpreter()).scan(png())
    assert result.restrictions == ()
    assert result.requires_human_review is True
    assert result.towing_risk_score == 70


@pytest.mark.parametrize("content", [b"", b"not-an-image"])
def test_rejects_empty_or_corrupt_images(content: bytes) -> None:
    scanner = SignScannerService(FakeOcr("NO PARKING"), SignInterpreter())
    with pytest.raises(InvalidSignImageError):
        scanner.scan(content)


def test_authenticated_scanner_api_is_non_cacheable() -> None:
    application = create_app()
    application.dependency_overrides[current_user] = lambda: User(
        uuid4(),
        "driver@example.com",
        "hash",
        Role.USER,
        True,
        True,
        datetime.now(UTC),
    )
    application.dependency_overrides[sign_scanner_service] = lambda: SignScannerService(
        FakeOcr("RESIDENT PERMIT ONLY"), SignInterpreter()
    )
    with TestClient(application) as client:
        response = client.post(
            "/api/v1/signs/scan",
            files={"image": ("sign.png", png(), "image/png")},
        )

    assert response.status_code == 200
    assert response.json()["towing_risk_score"] == 80
    assert response.json()["provider_version"] == "fake-ocr-1"
    assert response.headers["Cache-Control"] == "no-store"


def test_scanner_api_rejects_non_image_content_type() -> None:
    application = create_app()
    application.dependency_overrides[current_user] = lambda: User(
        uuid4(), "driver@example.com", "hash", Role.USER, True, True, datetime.now(UTC)
    )
    with TestClient(application) as client:
        response = client.post(
            "/api/v1/signs/scan",
            files={"image": ("sign.txt", b"text", "text/plain")},
        )

    assert response.status_code == 415
