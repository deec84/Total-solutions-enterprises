"""Authenticated parking-sign upload and analysis endpoint."""

import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status

from app.modules.identity.domain import User
from app.modules.sign_scanner.interpreter import SignInterpreter
from app.modules.sign_scanner.ocr import TesseractOcrProvider
from app.modules.sign_scanner.schemas import SignScanResponse
from app.modules.sign_scanner.service import (
    MAX_IMAGE_BYTES,
    InvalidSignImageError,
    SignScannerService,
)
from app.presentation.api.routes.auth import current_user

router = APIRouter()
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
_scanner = SignScannerService(TesseractOcrProvider(), SignInterpreter())


def sign_scanner_service() -> SignScannerService:
    return _scanner


@router.post("/scan", response_model=SignScanResponse)
async def scan_sign(
    _: Annotated[User, Depends(current_user)],
    scanner: Annotated[SignScannerService, Depends(sign_scanner_service)],
    response: Response,
    image: Annotated[UploadFile, File(description="JPEG, PNG, or WebP parking sign")],
) -> SignScanResponse:
    response.headers["Cache-Control"] = "no-store"
    if image.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "unsupported image type")
    content = await image.read(MAX_IMAGE_BYTES + 1)
    await image.close()
    try:
        result = await asyncio.to_thread(scanner.scan, content)
    except InvalidSignImageError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    return SignScanResponse(
        detected_text=result.detected_text,
        redacted_text=result.redacted_text,
        language=result.language,
        summary=result.summary,
        restrictions=list(result.restrictions),
        towing_risk_score=result.towing_risk_score,
        confidence=result.confidence,
        requires_human_review=result.requires_human_review,
        provider_version=result.provider_version,
        disclaimer="AI and OCR can be wrong. Follow the current physical sign and official rules.",
    )
