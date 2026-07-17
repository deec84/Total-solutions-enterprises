import asyncio
from datetime import UTC, datetime
from io import BytesIO
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import create_app
from app.modules.community.domain import ReportCategory, ReportStatus
from app.modules.community.repositories import InMemoryCommunityReportRepository
from app.modules.community.schemas import AppealResolution, ModerationCommand
from app.modules.community.service import (
    CommunityReportService,
    DuplicateReportError,
    InvalidReportError,
)
from app.modules.identity.domain import Role, User
from app.presentation.api.routes.auth import current_user
from app.presentation.api.routes.community import (
    community_media_store,
    community_repository,
    moderate_report,
    resolve_appeal,
)


class FakeAdminAudit:
    def __init__(self) -> None:
        self.events: list[tuple[object, str, object]] = []

    async def append(self, actor_id: object, action: str, subject_id: object) -> None:
        self.events.append((actor_id, action, subject_id))


def _png() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (80, 80), "white").save(buffer, "PNG")
    return buffer.getvalue()


def _application(
    media_store: object | None = None,
) -> tuple[TestClient, InMemoryCommunityReportRepository]:
    repository = InMemoryCommunityReportRepository()
    user = User(
        uuid4(), "reporter@example.com", "hash", Role.USER, True, True, datetime.now(UTC)
    )
    application = create_app()
    application.dependency_overrides[current_user] = lambda: user
    application.dependency_overrides[community_repository] = lambda: repository
    if media_store is not None:
        application.dependency_overrides[community_media_store] = lambda: media_store
    return TestClient(application), repository


def test_detailed_report_with_photo_is_published() -> None:
    async def scenario() -> None:
        repository = InMemoryCommunityReportRepository()
        service = CommunityReportService(repository)
        report = await service.submit(
            uuid4(),
            ReportCategory.TOWING,
            25.7617,
            -80.1918,
            "Tow truck removed a vehicle beside the red curb at 10:30 PM.",
            b"validated-photo",
        )
        assert report.status is ReportStatus.PUBLISHED
        assert report.photo_sha256 is not None
        assert await repository.pending(10) == ()

    asyncio.run(scenario())


def test_low_evidence_report_enters_isolated_moderation_queue() -> None:
    async def scenario() -> None:
        repository = InMemoryCommunityReportRepository()
        report = await CommunityReportService(repository).submit(
            uuid4(), ReportCategory.SIGN, 25.7, -80.2, "New restriction sign"
        )
        assert report.status is ReportStatus.PENDING
        assert (await repository.pending(10))[0].id == report.id

    asyncio.run(scenario())


def test_duplicate_within_24_hours_is_rejected() -> None:
    async def scenario() -> None:
        service = CommunityReportService(InMemoryCommunityReportRepository())
        reporter = uuid4()
        args = (reporter, ReportCategory.PRICE, 25.7, -80.2, "Storage price is now 250 dollars")
        await service.submit(*args)
        with pytest.raises(DuplicateReportError):
            await service.submit(*args)

    asyncio.run(scenario())


def test_moderator_can_publish_and_rejects_missing_reason() -> None:
    async def scenario() -> None:
        repository = InMemoryCommunityReportRepository()
        service = CommunityReportService(repository)
        report = await service.submit(
            uuid4(), ReportCategory.RESTRICTION, 25.7, -80.2, "Permit rule changed"
        )
        with pytest.raises(InvalidReportError):
            await service.moderate(report.id, True, "no")
        updated = await service.moderate(report.id, True, "Verified against sign photo")
        assert updated.status is ReportStatus.PUBLISHED
        assert updated.moderation_reason == "Verified against sign photo"
        reputation = await repository.reputation(report.reporter_id)
        assert reputation.score == 0.55
        assert reputation.approved_reports == 1

    asyncio.run(scenario())


def test_reporter_can_appeal_rejection_once_and_moderator_can_overturn() -> None:
    async def scenario() -> None:
        reporter = uuid4()
        repository = InMemoryCommunityReportRepository()
        service = CommunityReportService(repository)
        report = await service.submit(
            reporter, ReportCategory.SIGN, 25.7, -80.2, "A recently installed permit sign"
        )
        await service.moderate(report.id, False, "Photo did not show the full sign")
        appeal = await service.appeal(
            report.id, reporter, "I can provide the original uncropped photo"
        )
        with pytest.raises(DuplicateReportError):
            await service.appeal(report.id, reporter, "A second duplicate appeal reason")
        resolved = await service.resolve_appeal(
            appeal.id, True, "Original image confirms the restriction"
        )
        assert resolved.status.value == "overturned"
        assert (await repository.get(report.id)).status is ReportStatus.PUBLISHED  # type: ignore[union-attr]

    asyncio.run(scenario())


def test_only_owner_can_appeal_a_rejected_report() -> None:
    async def scenario() -> None:
        owner = uuid4()
        repository = InMemoryCommunityReportRepository()
        service = CommunityReportService(repository)
        report = await service.submit(
            owner, ReportCategory.TOWING, 25.7, -80.2, "A vehicle was removed near this address"
        )
        with pytest.raises(InvalidReportError):
            await service.appeal(report.id, uuid4(), "This report belongs to someone else")

    asyncio.run(scenario())


def test_invalid_submission_and_unknown_report_are_rejected() -> None:
    async def scenario() -> None:
        service = CommunityReportService(InMemoryCommunityReportRepository())
        with pytest.raises(InvalidReportError):
            await service.submit(uuid4(), ReportCategory.SIGN, 0, 0, "short")
        with pytest.raises(InvalidReportError):
            await service.moderate(uuid4(), False, "Fraud signal confirmed")

    asyncio.run(scenario())


def test_authenticated_json_submission_contract() -> None:
    client, _ = _application()
    with client:
        response = client.post(
            "/api/v1/reports",
            json={
                "category": "restriction",
                "latitude": 25.7617,
                "longitude": -80.1918,
                "description": "A temporary restriction was posted this morning",
            },
        )
    assert response.status_code == 201
    assert response.json()["status"] == "pending"
    assert response.json()["validation_score"] == 0.65


def test_photo_submission_validates_media_and_publishes_evidence() -> None:
    client, _ = _application()
    form = {
        "category": "towing",
        "latitude": "25.7617",
        "longitude": "-80.1918",
        "description": "Tow vehicles were active beside this red curb after ten PM",
    }
    with client:
        unsupported = client.post(
            "/api/v1/reports/with-photo",
            data=form,
            files={"photo": ("evidence.txt", b"bad", "text/plain")},
        )
        accepted = client.post(
            "/api/v1/reports/with-photo",
            data=form,
            files={"photo": ("evidence.png", _png(), "image/png")},
        )
    assert unsupported.status_code == 415
    assert accepted.status_code == 201
    assert accepted.json()["status"] == "published"
    assert accepted.json()["photo_sha256"] is not None
    assert accepted.json()["photo_available"] is False


def test_photo_submission_rejects_corrupt_image() -> None:
    client, _ = _application()
    with client:
        response = client.post(
            "/api/v1/reports/with-photo",
            data={
                "category": "sign",
                "latitude": "25.7",
                "longitude": "-80.2",
                "description": "This parking sign appears to have changed recently",
            },
            files={"photo": ("bad.png", b"not-image", "image/png")},
        )
    assert response.status_code == 422


def test_privileged_mutations_append_actor_and_subject_to_audit_chain() -> None:
    async def scenario() -> None:
        reporter_id, actor_id = uuid4(), uuid4()
        actor = User(
            actor_id, "admin@example.com", "hash", Role.ADMIN, True, True, datetime.now(UTC)
        )
        repository = InMemoryCommunityReportRepository()
        service = CommunityReportService(repository)
        audit = FakeAdminAudit()
        report = await service.submit(
            reporter_id,
            ReportCategory.RESTRICTION,
            25.7,
            -80.2,
            "A permit-only restriction was recently posted",
        )
        await moderate_report(
            report.id,
            ModerationCommand(approved=False, reason="Evidence requires clarification"),
            actor,
            repository,  # type: ignore[arg-type]
            audit,  # type: ignore[arg-type]
            None,
        )
        appeal = await service.appeal(
            report.id, reporter_id, "The original image includes the entire sign"
        )
        await resolve_appeal(
            appeal.id,
            AppealResolution(overturned=True, reason="Full image confirms restriction"),
            actor,
            repository,  # type: ignore[arg-type]
            audit,  # type: ignore[arg-type]
        )
        assert audit.events == [
            (actor_id, "community.report_rejected", report.id),
            (actor_id, "community.appeal_overturned", report.id),
        ]

    asyncio.run(scenario())
