"""Strict offline connectors for municipal GeoJSON zones and CSV facilities."""

import csv
import hashlib
import io
import json
from datetime import datetime
from urllib.parse import urlparse

from pydantic import BaseModel, Field, ValidationError

from app.modules.ingestion.domain import (
    NormalizedImport,
    NormalizedParkingFacility,
    NormalizedParkingZone,
    RejectedRecord,
)
from app.modules.parking.domain import ZoneType

IMPORTER_VERSION = "1.0"
MAX_RECORDS = 5_000


class ZoneProperties(BaseModel):
    external_id: str = Field(min_length=1, max_length=160)
    name: str = Field(min_length=1, max_length=160)
    zone_type: ZoneType
    parking_score: int = Field(ge=0, le=100)
    restriction_summary: str | None = Field(default=None, max_length=2_000)
    average_towing_cost_cents: int | None = Field(default=None, ge=0, le=1_000_000)
    towing_hotspot: bool = False
    observed_at: datetime
    expires_at: datetime | None = None


class ZoneGeometry(BaseModel):
    type: str
    coordinates: list[list[list[float]]]


class ZoneFeature(BaseModel):
    type: str
    properties: ZoneProperties
    geometry: ZoneGeometry


def _hash(value: object) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), default=str
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _reject(index: int, value: object, code: str, detail: str) -> RejectedRecord:
    return RejectedRecord(index, _hash(value), code, detail[:500])


def _aware_timestamps(observed_at: datetime, expires_at: datetime | None) -> None:
    if observed_at.tzinfo is None or (expires_at is not None and expires_at.tzinfo is None):
        raise ValueError("timestamps must include a timezone")
    if expires_at is not None and expires_at <= observed_at:
        raise ValueError("expires_at must be later than observed_at")


class GeoJsonParkingZoneConnector:
    def parse(self, payload: bytes) -> NormalizedImport:
        try:
            document = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            rejection = _reject(-1, payload.hex(), "invalid_json", "feed is not UTF-8 JSON")
            return NormalizedImport(1, rejected=(rejection,))
        if not isinstance(document, dict) or document.get("type") != "FeatureCollection":
            rejection = _reject(
                -1, document, "invalid_collection", "root must be a GeoJSON FeatureCollection"
            )
            return NormalizedImport(1, rejected=(rejection,))
        features = document.get("features")
        if not isinstance(features, list) or len(features) > MAX_RECORDS:
            rejection = _reject(
                -1,
                document,
                "invalid_record_count",
                f"features must be a list with at most {MAX_RECORDS} records",
            )
            return NormalizedImport(1, rejected=(rejection,))

        accepted: list[NormalizedParkingZone] = []
        rejected: list[RejectedRecord] = []
        seen: set[str] = set()
        for index, raw in enumerate(features):
            try:
                feature = ZoneFeature.model_validate(raw)
                if feature.type != "Feature" or feature.geometry.type != "Polygon":
                    raise ValueError("only GeoJSON Polygon features are supported")
                if feature.properties.external_id in seen:
                    raise ValueError("external_id is duplicated in this batch")
                self._validate_polygon(feature.geometry.coordinates)
                _aware_timestamps(
                    feature.properties.observed_at, feature.properties.expires_at
                )
                seen.add(feature.properties.external_id)
                accepted.append(
                    NormalizedParkingZone(
                        external_id=feature.properties.external_id,
                        name=feature.properties.name,
                        zone_type=feature.properties.zone_type,
                        geometry_geojson=json.dumps(
                            feature.geometry.model_dump(), separators=(",", ":")
                        ),
                        parking_score=feature.properties.parking_score,
                        restriction_summary=feature.properties.restriction_summary,
                        average_towing_cost_cents=(
                            feature.properties.average_towing_cost_cents
                        ),
                        towing_hotspot=feature.properties.towing_hotspot,
                        observed_at=feature.properties.observed_at,
                        expires_at=feature.properties.expires_at,
                    )
                )
            except (ValidationError, ValueError):
                rejected.append(
                    _reject(
                        index,
                        raw,
                        "invalid_zone",
                        "record does not satisfy the parking-zone contract",
                    )
                )
        return NormalizedImport(len(features), zones=tuple(accepted), rejected=tuple(rejected))

    @staticmethod
    def _validate_polygon(coordinates: list[list[list[float]]]) -> None:
        if not coordinates:
            raise ValueError("polygon must contain at least one ring")
        for ring in coordinates:
            if len(ring) < 4 or ring[0] != ring[-1]:
                raise ValueError("polygon rings must be closed with at least four points")
            for coordinate in ring:
                if len(coordinate) != 2:
                    raise ValueError("polygon coordinates must contain longitude and latitude")
                longitude, latitude = coordinate
                if not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
                    raise ValueError("polygon coordinates are outside WGS84 bounds")


class CsvParkingFacilityConnector:
    required_fields = frozenset(
        {
            "external_id",
            "name",
            "address",
            "latitude",
            "longitude",
            "safety_score",
            "towing_incidents_per_1000",
            "navigation_url",
            "observed_at",
        }
    )

    def parse(self, payload: bytes) -> NormalizedImport:
        try:
            text = payload.decode("utf-8-sig")
        except UnicodeDecodeError:
            return NormalizedImport(
                1,
                rejected=(
                    _reject(-1, payload.hex(), "invalid_csv", "feed is not UTF-8 CSV"),
                ),
            )
        reader = csv.DictReader(io.StringIO(text))
        headers = frozenset(reader.fieldnames or ())
        if not self.required_fields.issubset(headers):
            return NormalizedImport(
                1,
                rejected=(
                    _reject(
                        -1,
                        sorted(headers),
                        "missing_columns",
                        "CSV is missing one or more required columns",
                    ),
                ),
            )
        rows = list(reader)
        if len(rows) > MAX_RECORDS:
            return NormalizedImport(
                1,
                rejected=(
                    _reject(
                        -1,
                        len(rows),
                        "invalid_record_count",
                        f"CSV must contain at most {MAX_RECORDS} records",
                    ),
                ),
            )

        accepted: list[NormalizedParkingFacility] = []
        rejected: list[RejectedRecord] = []
        seen: set[str] = set()
        for index, row in enumerate(rows):
            try:
                facility = self._row(row)
                if facility.external_id in seen:
                    raise ValueError("external_id is duplicated in this batch")
                seen.add(facility.external_id)
                accepted.append(facility)
            except (TypeError, ValueError):
                rejected.append(
                    _reject(
                        index,
                        row,
                        "invalid_facility",
                        "record does not satisfy the parking-facility contract",
                    )
                )
        return NormalizedImport(
            len(rows), facilities=tuple(accepted), rejected=tuple(rejected)
        )

    @staticmethod
    def _row(row: dict[str, str | None]) -> NormalizedParkingFacility:
        external_id = _required(row, "external_id", 160)
        name = _required(row, "name", 160)
        address = _required(row, "address", 500)
        latitude = _float(row, "latitude", -90, 90)
        longitude = _float(row, "longitude", -180, 180)
        safety_score = _int(row, "safety_score", 0, 100)
        towing_frequency = _float(row, "towing_incidents_per_1000", 0, 1000)
        navigation_url = _required(row, "navigation_url", 1000)
        if urlparse(navigation_url).scheme != "https":
            raise ValueError("navigation_url must use HTTPS")
        observed_at = _datetime(row, "observed_at", required=True)
        if observed_at is None:
            raise ValueError("observed_at is required")
        expires_at = _datetime(row, "expires_at", required=False)
        _aware_timestamps(observed_at, expires_at)
        hourly_price = _optional_int(row, "hourly_price_cents", 0, 1_000_000)
        rating = _optional_float(row, "rating", 0, 5)
        capacity = _optional_int(row, "capacity", 0, 1_000_000)
        available = _optional_int(row, "available_spaces", 0, 1_000_000)
        if available is not None and capacity is not None and available > capacity:
            raise ValueError("available_spaces cannot exceed capacity")
        return NormalizedParkingFacility(
            external_id,
            name,
            address,
            latitude,
            longitude,
            hourly_price,
            safety_score,
            towing_frequency,
            rating,
            available,
            capacity,
            navigation_url,
            observed_at,
            expires_at,
        )


def _required(row: dict[str, str | None], key: str, maximum: int) -> str:
    value = (row.get(key) or "").strip()
    if not value or len(value) > maximum:
        raise ValueError(f"{key} is required and must contain at most {maximum} characters")
    return value


def _float(row: dict[str, str | None], key: str, minimum: float, maximum: float) -> float:
    value = float(_required(row, key, 64))
    if not minimum <= value <= maximum:
        raise ValueError(f"{key} is outside the allowed range")
    return value


def _int(row: dict[str, str | None], key: str, minimum: int, maximum: int) -> int:
    value = int(_required(row, key, 32))
    if not minimum <= value <= maximum:
        raise ValueError(f"{key} is outside the allowed range")
    return value


def _optional_int(
    row: dict[str, str | None], key: str, minimum: int, maximum: int
) -> int | None:
    value = (row.get(key) or "").strip()
    return _int({key: value}, key, minimum, maximum) if value else None


def _optional_float(
    row: dict[str, str | None], key: str, minimum: float, maximum: float
) -> float | None:
    value = (row.get(key) or "").strip()
    return _float({key: value}, key, minimum, maximum) if value else None


def _datetime(
    row: dict[str, str | None], key: str, *, required: bool
) -> datetime | None:
    value = (row.get(key) or "").strip()
    if not value and not required:
        return None
    if not value:
        raise ValueError(f"{key} is required")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
