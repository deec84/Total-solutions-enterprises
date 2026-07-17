import asyncio
import hashlib
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from io import BytesIO
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import create_app
from app.modules.community.domain import CommunityReport, ReportCategory, ReportStatus
from app.modules.community.media import (
    CommunityMediaLifecycle,
    MediaStorageError,
    MediaUnavailableError,
)
from app.modules.community.repositories import InMemoryCommunityReportRepository
from app.modules.community.s3_media import S3CommunityMediaStore
from app.modules.community.service import CommunityReportService, InvalidReportError
from app.modules.identity.domain import Role, User
from app.presentation.api.routes.admin import privileged_user
from app.presentation.api.routes.auth import current_user
from app.presentation.api.routes.community import (
    admin_audit_trail,
    community_media_store,
    community_repository,
    purge_report_media,
)


def png() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (64, 64), "white").save(buffer, "PNG")
    return buffer.getvalue()


class FakeMediaStore:
    def __init__(self) -> None:
        self.objects: dict[str, dict[str, object]] = {}
        self.deleted: list[str] = []
        self.fail_put = False
        self.fail_delete: set[str] = set()

    async def put(self, **values: object) -> None:
        if self.fail_put:
            raise MediaStorageError("object store unavailable")
        key = str(values["key"])
        self.objects[key] = values

    async def delete(self, key: str) -> None:
        if key in self.fail_delete:
            raise MediaStorageError("object deletion unavailable")
        self.deleted.append(key)
        self.objects.pop(key, None)

    async def create_read_url(self, key: str, expires_seconds: int) -> str:
        if key in self.fail_delete:
            raise MediaStorageError("object access unavailable")
        return f"https://media.example.test/{key}?expires={expires_seconds}"


class FakeS3Client:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.puts: list[dict[str, object]] = []
        self.deletes: list[dict[str, object]] = []

    def put_object(self, **kwargs: object) -> object:
        if self.fail:
            raise OSError("S3 unavailable")
        self.puts.append(kwargs)
        return {}

    def delete_object(self, **kwargs: object) -> object:
        if self.fail:
            raise OSError("S3 unavailable")
        self.deletes.append(kwargs)
        return {}

    def generate_presigned_url(
        self,
        client_method: str,
        *,
        Params: dict[str, str],
        ExpiresIn: int,
    ) -> str:
        if self.fail:
            raise OSError("S3 unavailable")
        assert client_method == "get_object"
        return f"https://private-media.s3.amazonaws.com/{Params['Key']}?expires={ExpiresIn}"


class FakeAudit:
    def __init__(self) -> None:
        self.events: list[tuple[object, str, object | None]] = []

    async def append(self, actor_id: object, action: str, subject_id: object | None = None) -> None:
        self.events.append((actor_id, action, subject_id))


class RecordingRepository(InMemoryCommunityReportRepository):
    def __init__(self) -> None:
        super().__init__()
        self.add_count = 0

    async def add(self, report: CommunityReport) -> None:
        self.add_count += 1
        await super().add(report)


class FailingRepository(InMemoryCommunityReportRepository):
    async def add(self, report: CommunityReport) -> None:
        raise RuntimeError("database unavailable")


class FailingCleanupStore(FakeMediaStore):
    async def delete(self, key: str) -> None:
        raise MediaStorageError("cleanup unavailable")


def test_governed_photo_is_stored_and_rejection_deletes_it() -> None:
    async def scenario() -> None:
        repository = InMemoryCommunityReportRepository()
        store = FakeMediaStore()
        lifecycle = CommunityMediaLifecycle(repository, store)
        payload = png()
        report = await CommunityReportService(repository, lifecycle).submit(
            uuid4(),
            ReportCategory.TOWING,
            25.7617,
            -80.1918,
            "Tow activity was photographed beside the restricted curb after ten PM",
            payload,
            "image/png",
        )

        assert report.photo_available
        assert report.photo_size_bytes == len(payload)
        assert report.photo_content_type == "image/png"
        assert report.photo_object_key in store.objects
        assert report.photo_object_key is not None
        stored = store.objects[report.photo_object_key]
        assert stored["checksum_sha256"] == hashlib.sha256(payload).hexdigest()
        assert report.photo_retained_until == stored["retained_until"]

        grant = await lifecycle.create_access_grant(report.id, expires_seconds=90)
        assert grant.url.startswith("https://media.example.test/community-reports/")
        assert grant.expires_at > datetime.now(UTC)

        rejected = await CommunityReportService(repository, lifecycle).moderate(
            report.id, False, "The image does not show the full restriction"
        )
        assert rejected.status is ReportStatus.REJECTED
        assert not rejected.photo_available
        assert rejected.photo_deleted_at is not None
        assert store.deleted == [report.photo_object_key]
        with pytest.raises(MediaUnavailableError):
            await lifecycle.create_access_grant(report.id)

    asyncio.run(scenario())


def test_expired_media_purge_is_bounded_and_retryable() -> None:
    async def scenario() -> None:
        repository = InMemoryCommunityReportRepository()
        store = FakeMediaStore()
        lifecycle = CommunityMediaLifecycle(repository, store, retention_days=1)
        service = CommunityReportService(repository, lifecycle)
        first = await service.submit(
            uuid4(),
            ReportCategory.SIGN,
            25.7,
            -80.2,
            "The complete restriction sign is visible in this photograph",
            b"first-photo",
            "image/jpeg",
        )
        second = await service.submit(
            uuid4(),
            ReportCategory.PRICE,
            25.8,
            -80.3,
            "The posted garage price and operating hours are visible here",
            b"second-photo",
            "image/webp",
        )
        cutoff = datetime.now(UTC)
        first = replace(first, photo_retained_until=cutoff - timedelta(minutes=2))
        second = replace(second, photo_retained_until=cutoff - timedelta(minutes=1))
        await repository.add(first)
        await repository.add(second)
        assert second.photo_object_key is not None
        store.fail_delete.add(second.photo_object_key)

        result = await lifecycle.purge_expired(cutoff, limit=2)

        assert (result.scanned, result.deleted, result.failed) == (2, 1, 1)
        assert not (await repository.get(first.id)).photo_available  # type: ignore[union-attr]
        assert (await repository.get(second.id)).photo_available  # type: ignore[union-attr]

    asyncio.run(scenario())


def test_media_lifecycle_rejects_unsafe_inputs() -> None:
    async def scenario() -> None:
        repository = InMemoryCommunityReportRepository()
        store = FakeMediaStore()
        with pytest.raises(ValueError, match="retention"):
            CommunityMediaLifecycle(repository, store, retention_days=0)
        lifecycle = CommunityMediaLifecycle(repository, store)
        checksum = hashlib.sha256(b"photo").hexdigest()
        with pytest.raises(ValueError, match="type"):
            await lifecycle.store(uuid4(), b"photo", "text/plain", checksum, datetime.now(UTC))
        with pytest.raises(ValueError, match="checksum"):
            await lifecycle.store(uuid4(), b"photo", "image/png", "0" * 64, datetime.now(UTC))
        with pytest.raises(ValueError, match="timezone"):
            await lifecycle.store(uuid4(), b"photo", "image/png", checksum, datetime.now())
        with pytest.raises(ValueError, match="limit"):
            await lifecycle.purge_expired(limit=0)
        with pytest.raises(ValueError, match="lifetime"):
            await lifecycle.create_access_grant(uuid4(), expires_seconds=10)
        with pytest.raises(MediaUnavailableError):
            await lifecycle.create_access_grant(uuid4())
        report_without_photo = await CommunityReportService(repository).submit(
            uuid4(),
            ReportCategory.RESTRICTION,
            25.7,
            -80.2,
            "A permit-only restriction was posted beside the parking lane",
        )
        assert await lifecycle.delete_report_photo(report_without_photo) == report_without_photo

    asyncio.run(scenario())


def test_service_requires_content_type_when_governed_storage_is_enabled() -> None:
    async def scenario() -> None:
        repository = InMemoryCommunityReportRepository()
        lifecycle = CommunityMediaLifecycle(repository, FakeMediaStore())
        with pytest.raises(InvalidReportError, match="content type"):
            await CommunityReportService(repository, lifecycle).submit(
                uuid4(),
                ReportCategory.SIGN,
                25.7,
                -80.2,
                "The entire restriction sign is clearly visible in this image",
                b"photo",
            )

    asyncio.run(scenario())


def test_report_persistence_failure_compensates_the_uploaded_object() -> None:
    async def scenario() -> None:
        store = FakeMediaStore()
        repository = FailingRepository()
        lifecycle = CommunityMediaLifecycle(repository, store)
        with pytest.raises(RuntimeError, match="database"):
            await CommunityReportService(repository, lifecycle).submit(
                uuid4(),
                ReportCategory.SIGN,
                25.7,
                -80.2,
                "The complete restriction sign is visible in this photograph",
                b"evidence",
                "image/jpeg",
            )
        assert store.objects == {}
        assert len(store.deleted) == 1

        broken_cleanup = FailingCleanupStore()
        broken_lifecycle = CommunityMediaLifecycle(repository, broken_cleanup)
        with pytest.raises(MediaStorageError, match="cleanup failed"):
            await CommunityReportService(repository, broken_lifecycle).submit(
                uuid4(),
                ReportCategory.TOWING,
                25.8,
                -80.3,
                "The complete tow notice is visible in this retained photograph",
                b"evidence-two",
                "image/png",
            )

    asyncio.run(scenario())


def test_s3_adapter_sets_integrity_metadata_and_wraps_provider_errors() -> None:
    async def scenario() -> None:
        payload = b"evidence"
        checksum = hashlib.sha256(payload).hexdigest()
        retained_until = datetime.now(UTC) + timedelta(days=30)
        client = FakeS3Client()
        store = S3CommunityMediaStore("private-media", client)
        key = f"community-reports/{uuid4()}/{checksum}"

        await store.put(
            key=key,
            payload=payload,
            content_type="image/jpeg",
            checksum_sha256=checksum,
            retained_until=retained_until,
        )
        await store.delete(key)
        url = await store.create_read_url(key, 60)

        assert client.puts[0]["Bucket"] == "private-media"
        assert client.puts[0]["CacheControl"] == "private, no-store"
        assert client.puts[0]["Metadata"] == {
            "sha256": checksum,
            "retained-until": retained_until.isoformat(),
        }
        assert client.deletes == [{"Bucket": "private-media", "Key": key}]
        assert url.startswith("https://private-media.s3.amazonaws.com/")

        with pytest.raises(ValueError, match="object key"):
            await store.delete("../unsafe")
        broken = S3CommunityMediaStore("private-media", FakeS3Client(fail=True))
        with pytest.raises(MediaStorageError, match="storage"):
            await broken.put(
                key=key,
                payload=payload,
                content_type="image/jpeg",
                checksum_sha256=checksum,
                retained_until=retained_until,
            )
        with pytest.raises(MediaStorageError, match="deletion"):
            await broken.delete(key)
        with pytest.raises(MediaStorageError, match="access"):
            await broken.create_read_url(key, 60)

    asyncio.run(scenario())


def test_s3_adapter_can_build_its_client_from_the_aws_sdk(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = FakeS3Client()

    class FakeBoto3:
        @staticmethod
        def client(service: str) -> FakeS3Client:
            assert service == "s3"
            return client

    monkeypatch.setattr("app.modules.community.s3_media.import_module", lambda _: FakeBoto3())
    assert S3CommunityMediaStore("private-media")._client is client
    with pytest.raises(ValueError, match="bucket"):
        S3CommunityMediaStore("  ", client)


def test_photo_api_persists_governed_media_without_exposing_object_key() -> None:
    store = FakeMediaStore()
    repository = RecordingRepository()
    user = User(uuid4(), "media@example.com", "hash", Role.USER, True, True, datetime.now(UTC))
    application = create_app()
    application.dependency_overrides[current_user] = lambda: user
    application.dependency_overrides[community_repository] = lambda: repository
    application.dependency_overrides[community_media_store] = lambda: store

    with TestClient(application) as client:
        response = client.post(
            "/api/v1/reports/with-photo",
            data={
                "category": "towing",
                "latitude": "25.7617",
                "longitude": "-80.1918",
                "description": "Tow activity was photographed beside this restricted curb",
            },
            files={"photo": ("evidence.png", png(), "image/png")},
        )

    body = response.json()
    assert response.status_code == 201
    assert body["photo_available"] is True
    assert body["photo_retained_until"] is not None
    assert "photo_object_key" not in body
    assert len(store.objects) == 1
    assert repository.add_count == 1


def test_photo_api_fails_closed_when_object_storage_is_unavailable() -> None:
    store = FakeMediaStore()
    store.fail_put = True
    repository = RecordingRepository()
    user = User(uuid4(), "media@example.com", "hash", Role.USER, True, True, datetime.now(UTC))
    application = create_app()
    application.dependency_overrides[current_user] = lambda: user
    application.dependency_overrides[community_repository] = lambda: repository
    application.dependency_overrides[community_media_store] = lambda: store

    with TestClient(application) as client:
        response = client.post(
            "/api/v1/reports/with-photo",
            data={
                "category": "sign",
                "latitude": "25.7",
                "longitude": "-80.2",
                "description": "The complete restriction sign is visible in this photograph",
            },
            files={"photo": ("evidence.png", png(), "image/png")},
        )

    assert response.status_code == 503
    assert repository.add_count == 0


def test_admin_can_purge_expired_media_and_action_is_audited() -> None:
    async def scenario() -> None:
        repository = InMemoryCommunityReportRepository()
        store = FakeMediaStore()
        lifecycle = CommunityMediaLifecycle(repository, store, retention_days=1)
        report = await CommunityReportService(repository, lifecycle).submit(
            uuid4(),
            ReportCategory.SIGN,
            25.7,
            -80.2,
            "The complete sign and surrounding curb are visible in this photo",
            b"evidence",
            "image/jpeg",
        )
        await repository.add(
            replace(report, photo_retained_until=datetime.now(UTC) - timedelta(minutes=1))
        )
        actor = User(
            uuid4(), "admin@example.com", "hash", Role.ADMIN, True, True, datetime.now(UTC)
        )
        audit = FakeAudit()

        result = await purge_report_media(
            actor,
            repository,  # type: ignore[arg-type]
            audit,  # type: ignore[arg-type]
            store,  # type: ignore[arg-type]
            10,
        )

        assert (result.scanned, result.deleted, result.failed) == (1, 1, 0)
        assert audit.events == [(actor.id, "community.media_purged", None)]

    asyncio.run(scenario())


def test_media_dependencies_remain_overrideable_without_real_aws() -> None:
    application = create_app()
    repository = InMemoryCommunityReportRepository()
    store = FakeMediaStore()
    audit = FakeAudit()
    actor = User(uuid4(), "admin@example.com", "hash", Role.ADMIN, True, True, datetime.now(UTC))
    application.dependency_overrides[privileged_user] = lambda: actor
    application.dependency_overrides[community_repository] = lambda: repository
    application.dependency_overrides[community_media_store] = lambda: store
    application.dependency_overrides[admin_audit_trail] = lambda: audit

    with TestClient(application) as client:
        response = client.post("/api/v1/reports/media/purge?limit=1")

    assert response.status_code == 200
    assert response.json() == {"scanned": 0, "deleted": 0, "failed": 0}
    assert audit.events == [(actor.id, "community.media_purged", None)]


def test_privileged_media_access_is_short_lived_no_store_and_audited() -> None:
    repository = InMemoryCommunityReportRepository()
    store = FakeMediaStore()
    report = asyncio.run(
        CommunityReportService(repository, CommunityMediaLifecycle(repository, store)).submit(
            uuid4(),
            ReportCategory.SIGN,
            25.7,
            -80.2,
            "The complete restriction sign is visible in this retained evidence",
            b"evidence",
            "image/jpeg",
        )
    )
    audit = FakeAudit()
    actor = User(uuid4(), "admin@example.com", "hash", Role.ADMIN, True, True, datetime.now(UTC))
    application = create_app()
    application.dependency_overrides[privileged_user] = lambda: actor
    application.dependency_overrides[community_repository] = lambda: repository
    application.dependency_overrides[community_media_store] = lambda: store
    application.dependency_overrides[admin_audit_trail] = lambda: audit

    with TestClient(application) as client:
        response = client.get(f"/api/v1/reports/{report.id}/media-access?expires_seconds=90")

    assert response.status_code == 200
    assert response.json()["url"].startswith("https://media.example.test/")
    assert response.headers["Cache-Control"] == "private, no-store"
    assert response.headers["Pragma"] == "no-cache"
    assert audit.events == [(actor.id, "community.media_accessed", report.id)]
