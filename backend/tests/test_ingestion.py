"""Governed municipal connector, service, and API tests using synthetic data only."""

import asyncio
import json
from collections.abc import Iterator
from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import create_app
from app.modules.identity.domain import Role, User
from app.modules.ingestion.connectors import (
    CsvParkingFacilityConnector,
    GeoJsonParkingZoneConnector,
)
from app.modules.ingestion.domain import (
    DataFormat,
    FeedKind,
    ImportStatus,
    MunicipalConnector,
    MunicipalSource,
)
from app.modules.ingestion.repositories import InMemoryMunicipalIngestionRepository
from app.modules.ingestion.service import (
    MunicipalIngestionError,
    MunicipalIngestionService,
)
from app.presentation.api.routes.admin import privileged_user
from app.presentation.api.routes.ingestion import (
    ingestion_audit,
    municipal_ingestion_service,
)


def connectors() -> dict[tuple[FeedKind, DataFormat], MunicipalConnector]:
    return {
        (FeedKind.PARKING_ZONES, DataFormat.GEOJSON): GeoJsonParkingZoneConnector(),
        (FeedKind.PARKING_FACILITIES, DataFormat.CSV): CsvParkingFacilityConnector(),
    }


def zone_feature(
    external_id: str = "synthetic-zone-1", **properties: object
) -> dict[str, object]:
    values: dict[str, object] = {
        "external_id": external_id,
        "name": "SYNTHETIC TEST ZONE — NOT OFFICIAL",
        "zone_type": "towing_hotspot",
        "parking_score": 20,
        "restriction_summary": "Synthetic restriction for automated tests",
        "average_towing_cost_cents": 25000,
        "towing_hotspot": True,
        "observed_at": "2026-07-17T12:00:00Z",
        "expires_at": "2026-07-18T12:00:00Z",
    }
    values.update(properties)
    return {
        "type": "Feature",
        "properties": values,
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [-80.20, 25.70],
                    [-80.10, 25.70],
                    [-80.10, 25.80],
                    [-80.20, 25.70],
                ]
            ],
        },
    }


def geojson(*features: object) -> bytes:
    return json.dumps({"type": "FeatureCollection", "features": list(features)}).encode()


def facility_csv(*rows: str) -> bytes:
    header = (
        "external_id,name,address,latitude,longitude,hourly_price_cents,"
        "safety_score,towing_incidents_per_1000,rating,available_spaces,capacity,"
        "navigation_url,observed_at,expires_at\n"
    )
    return (header + "\n".join(rows) + "\n").encode()


def service(
    repository: InMemoryMunicipalIngestionRepository,
    maximum: int = 1024 * 1024,
) -> MunicipalIngestionService:
    return MunicipalIngestionService(repository, connectors(), maximum)


def test_geojson_connector_normalizes_valid_records_and_quarantines_invalid() -> None:
    invalid = zone_feature(
        "synthetic-zone-invalid",
        observed_at="2026-07-18T12:00:00Z",
        expires_at="2026-07-17T12:00:00Z",
    )
    parsed = GeoJsonParkingZoneConnector().parse(
        geojson(zone_feature(), invalid, zone_feature())
    )

    assert parsed.input_count == 3
    assert parsed.accepted_count == 1
    assert parsed.zones[0].external_id == "synthetic-zone-1"
    assert parsed.zones[0].towing_hotspot
    assert len(parsed.rejected) == 2
    assert all(len(item.record_sha256) == 64 for item in parsed.rejected)
    assert all("SYNTHETIC" not in item.reason_detail for item in parsed.rejected)


@pytest.mark.parametrize(
    "payload,code",
    [
        (b"not-json", "invalid_json"),
        (json.dumps([]).encode(), "invalid_collection"),
        (
            json.dumps({"type": "FeatureCollection", "features": "bad"}).encode(),
            "invalid_record_count",
        ),
    ],
)
def test_geojson_connector_rejects_invalid_feed_roots(payload: bytes, code: str) -> None:
    parsed = GeoJsonParkingZoneConnector().parse(payload)
    assert parsed.accepted_count == 0
    assert parsed.rejected[0].reason_code == code


@pytest.mark.parametrize(
    "mutation",
    [
        {"type": "LineString"},
        {"coordinates": []},
        {"coordinates": [[[-80.2, 25.7], [-80.1, 25.7], [-80.1, 25.8]]]},
        {"coordinates": [[[-180.2, 25.7], [-80.1, 25.7], [-80.1, 25.8], [-180.2, 25.7]]]},
        {"coordinates": [[[-80.2], [-80.1, 25.7], [-80.1, 25.8], [-80.2]]]},
    ],
)
def test_geojson_connector_rejects_unsafe_geometry(mutation: dict[str, object]) -> None:
    feature = zone_feature()
    geometry = feature["geometry"]
    assert isinstance(geometry, dict)
    geometry.update(mutation)
    parsed = GeoJsonParkingZoneConnector().parse(geojson(feature))
    assert parsed.accepted_count == 0
    assert parsed.rejected[0].reason_code == "invalid_zone"


def test_csv_connector_normalizes_synthetic_facilities_and_quarantines_bad_rows() -> None:
    valid = (
        "synthetic-facility-1,SYNTHETIC GARAGE — NOT OFFICIAL,100 Test Ave,"
        "25.7617,-80.1918,1200,90,1.5,4.5,10,100,https://example.test/nav,"
        "2026-07-17T12:00:00Z,2026-07-18T12:00:00Z"
    )
    invalid = (
        "synthetic-facility-2,Bad Garage,100 Test Ave,25.7,-80.2,,80,2.0,,11,10,"
        "http://example.test/nav,2026-07-17T12:00:00Z,"
    )
    parsed = CsvParkingFacilityConnector().parse(facility_csv(valid, invalid, valid))

    assert parsed.input_count == 3
    assert parsed.accepted_count == 1
    assert parsed.facilities[0].hourly_price_cents == 1200
    assert parsed.facilities[0].rating == 4.5
    assert len(parsed.rejected) == 2


def test_csv_connector_rejects_encoding_headers_ranges_and_naive_timestamps() -> None:
    connector = CsvParkingFacilityConnector()
    assert connector.parse(b"\xff").rejected[0].reason_code == "invalid_csv"
    assert connector.parse(b"name,address\nA,B\n").rejected[0].reason_code == "missing_columns"
    naive = (
        "synthetic-facility,Synthetic,Test,91,-80,,101,-1,,,0,"
        "https://example.test/nav,2026-07-17T12:00:00,"
    )
    parsed = connector.parse(facility_csv(naive))
    assert parsed.accepted_count == 0
    assert parsed.rejected[0].reason_code == "invalid_facility"
    secret_like_value = facility_csv(
        "synthetic-facility,Synthetic,Test,credential-like-value,-80,,80,2,,,,"
        "https://example.test/nav,2026-07-17T12:00:00Z,"
    )
    rejection = connector.parse(secret_like_value).rejected[0]
    assert "credential-like-value" not in rejection.reason_detail


def test_service_governs_sources_and_idempotent_imports() -> None:
    async def scenario() -> None:
        repository = InMemoryMunicipalIngestionRepository()
        ingestion = service(repository)
        source = await ingestion.create_source(
            name="  Synthetic Miami-Dade test feed  ",
            jurisdiction=" Miami-Dade test fixture ",
            feed_kind=FeedKind.PARKING_ZONES,
            data_format=DataFormat.GEOJSON,
            source_url="https://example.test/synthetic.geojson",
            license_url=None,
            official=False,
            refresh_interval_minutes=60,
            stale_after_minutes=120,
        )
        payload = geojson(zone_feature())
        first = await ingestion.import_payload(source.id, payload)
        replay = await ingestion.import_payload(source.id, payload)

        assert source.name == "Synthetic Miami-Dade test feed"
        assert source.provenance.value == "estimated"
        assert first.status is ImportStatus.COMMITTED
        assert replay.id == first.id
        assert len(await ingestion.sources()) == 1
        assert await ingestion.batches(source.id, 10) == (first,)
        assert repository.normalized(first.id).zones[0].name.startswith("SYNTHETIC")

    asyncio.run(scenario())


def test_service_rejects_unapproved_source_and_payload_contracts() -> None:
    async def scenario() -> None:
        repository = InMemoryMunicipalIngestionRepository()
        ingestion = service(repository, maximum=128)
        base = {
            "name": "Synthetic feed",
            "jurisdiction": "Test jurisdiction",
            "feed_kind": FeedKind.PARKING_ZONES,
            "data_format": DataFormat.GEOJSON,
            "source_url": "https://example.test/feed",
            "license_url": None,
            "official": False,
            "refresh_interval_minutes": 60,
            "stale_after_minutes": 120,
        }
        bad_values = [
            {"feed_kind": FeedKind.PARKING_FACILITIES, "data_format": DataFormat.GEOJSON},
            {"source_url": "http://example.test/feed"},
            {"source_url": "https://user:password@example.test/feed"},
            {"source_url": "https://example.test/feed?token=credential-like-value"},
            {"source_url": "https://example.test/feed#secret"},
            {"official": True},
            {"refresh_interval_minutes": 4},
            {"stale_after_minutes": 30},
            {"name": " "},
            {"jurisdiction": " "},
        ]
        for override in bad_values:
            with pytest.raises(MunicipalIngestionError):
                await ingestion.create_source(**(base | override))

        source = await ingestion.create_source(**base)
        with pytest.raises(MunicipalIngestionError, match="between"):
            await ingestion.import_payload(source.id, b"")
        with pytest.raises(MunicipalIngestionError, match="between"):
            await ingestion.import_payload(source.id, b"x" * 129)
        with pytest.raises(MunicipalIngestionError, match="not found"):
            await ingestion.import_payload(uuid4(), b"{}")
        with pytest.raises(MunicipalIngestionError, match="not found"):
            await ingestion.batches(uuid4(), 10)

        disabled = MunicipalSource(
            source.id,
            source.name,
            source.jurisdiction,
            source.feed_kind,
            source.data_format,
            source.source_url,
            source.license_url,
            source.official,
            False,
            source.refresh_interval_minutes,
            source.stale_after_minutes,
            source.created_at,
            source.updated_at,
        )
        await repository.add_source(disabled)
        with pytest.raises(MunicipalIngestionError, match="disabled"):
            await ingestion.import_payload(source.id, b"{}")

    asyncio.run(scenario())


class RecordingAudit:
    def __init__(self) -> None:
        self.actions: list[str] = []

    async def append(
        self, actor_id: UUID, action: str, subject_id: UUID | None = None
    ) -> object:
        self.actions.append(action)
        return object()


@pytest.fixture
def ingestion_api() -> Iterator[tuple[TestClient, RecordingAudit]]:
    repository = InMemoryMunicipalIngestionRepository()
    ingestion = service(repository)
    audit = RecordingAudit()
    actor = User(
        uuid4(),
        "admin@example.com",
        "hash",
        Role.ADMIN,
        True,
        True,
        datetime.now(UTC),
        "secret",
        True,
    )
    application = create_app()
    application.dependency_overrides[privileged_user] = lambda: actor
    application.dependency_overrides[municipal_ingestion_service] = lambda: ingestion
    application.dependency_overrides[ingestion_audit] = lambda: audit
    with TestClient(application) as client:
        yield client, audit
    application.dependency_overrides.clear()


def test_ingestion_api_creates_lists_imports_and_audits_synthetic_source(
    ingestion_api: tuple[TestClient, RecordingAudit],
) -> None:
    client, audit = ingestion_api
    created = client.post(
        "/api/v1/admin/data/sources",
        json={
            "name": "Synthetic Broward zones",
            "jurisdiction": "Broward test fixture",
            "feed_kind": "parking_zones",
            "data_format": "geojson",
            "source_url": "https://example.test/broward.geojson",
            "official": False,
            "refresh_interval_minutes": 60,
            "stale_after_minutes": 120,
        },
    )
    source_id = created.json()["id"]
    listed = client.get("/api/v1/admin/data/sources")
    imported = client.post(
        f"/api/v1/admin/data/sources/{source_id}/imports",
        files={"payload": ("synthetic.geojson", geojson(zone_feature()), "application/geo+json")},
    )
    batches = client.get(f"/api/v1/admin/data/sources/{source_id}/imports")

    assert created.status_code == 201
    assert created.json()["provenance"] == "estimated"
    assert listed.json()[0]["name"] == "Synthetic Broward zones"
    assert imported.status_code == 200
    assert imported.json()["status"] == "committed"
    assert batches.json()[0]["accepted_count"] == 1
    assert audit.actions == ["municipal.source_created", "municipal.import_committed"]


def test_ingestion_api_returns_safe_validation_and_disabled_errors(
    ingestion_api: tuple[TestClient, RecordingAudit],
) -> None:
    client, _ = ingestion_api
    invalid = client.post(
        "/api/v1/admin/data/sources",
        json={
            "name": "Claimed official source",
            "jurisdiction": "Test",
            "feed_kind": "parking_zones",
            "data_format": "geojson",
            "source_url": "https://example.test/feed",
            "official": True,
            "refresh_interval_minutes": 60,
            "stale_after_minutes": 120,
        },
    )
    missing = client.get(f"/api/v1/admin/data/sources/{uuid4()}/imports")
    assert invalid.status_code == 422
    assert missing.status_code == 404

    with pytest.raises(HTTPException) as error:
        municipal_ingestion_service(AsyncMock(spec=AsyncSession))
    assert error.value.status_code == 503
