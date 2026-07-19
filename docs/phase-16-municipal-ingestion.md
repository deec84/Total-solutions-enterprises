# Phase 16 — Governed municipal-data ingestion

## Outcome

ParkShield can register a municipal source and ingest supplied parking-zone or facility data through explicit, versioned contracts. The implementation does not fetch arbitrary URLs, use provider credentials, claim simulated data is official, or enable imports by default. It is the controlled ingestion boundary required before a Miami-Dade or Broward data agreement can be connected.

## Security and trust boundary

- All endpoints require a privileged role and completed MFA through the existing administration dependency.
- `PARKSHIELD_MUNICIPAL_IMPORTS_ENABLED` defaults to `false`; a disabled environment responds with HTTP 503.
- Source and license locations must be absolute HTTPS URLs without embedded credentials, query strings, or fragments. They are provenance metadata only; this phase never makes outbound requests.
- Uploads are bounded by `PARKSHIELD_MUNICIPAL_MAX_UPLOAD_BYTES` and 5,000 records.
- Parsing is offline, strict, timezone-aware, and limited to WGS84 coordinates.
- Rejected records are quarantined as SHA-256, record index, stable reason code, and bounded detail. Raw rejected feed records are not copied into the quarantine table.
- Replays of the same source/payload digest return the original batch rather than duplicating data.
- Accepted parking records retain both source and import-batch lineage. Upserts are keyed by source plus external record ID.
- Non-official sources always produce `estimated` provenance with conservative confidence. A public license URL is required before an administrator can mark a source official, but owner/legal verification remains a mandatory external gate.

## API

All paths are below `/api/v1/admin/data` and appear in the generated OpenAPI document.

| Method and path | Purpose |
|---|---|
| `POST /sources` | Register one governed source contract. |
| `GET /sources` | List configured sources and provenance. |
| `POST /sources/{source_id}/imports` | Upload one multipart `payload` using the source's approved connector. |
| `GET /sources/{source_id}/imports?limit=20` | List immutable batch results; limit is 1–100. |

Every import returns its SHA-256 digest, importer version, timestamps, status (`committed`, `partial`, or `rejected`), and accepted/rejected counts. Administrative source creation and imports are appended to the tamper-evident audit trail.

## Supported feed contracts

### Parking zones: GeoJSON

The root must be a `FeatureCollection`. Every feature must be a Polygon with closed rings and coordinates inside WGS84 bounds. Required properties are `external_id`, `name`, `zone_type`, `parking_score`, and timezone-aware `observed_at`. Optional properties are `restriction_summary`, `average_towing_cost_cents`, `towing_hotspot`, and timezone-aware `expires_at`. Expiry must be later than observation.

`zone_type` uses the existing API enum: `general`, `resident_only`, `private_property`, `commercial`, or `towing_hotspot`. `parking_score` is 0–100. Costs are nonnegative integer cents.

### Parking facilities: CSV

Required columns are `external_id`, `name`, `address`, `latitude`, `longitude`, `safety_score`, `towing_incidents_per_1000`, `navigation_url`, and `observed_at`. Optional columns are `hourly_price_cents`, `rating`, `available_spaces`, `capacity`, and `expires_at`.

Coordinates must be WGS84, safety is 0–100, rating is 0–5, navigation uses HTTPS, and timestamps include a timezone. Availability cannot exceed capacity.

The automated fixtures deliberately use names such as `SYNTHETIC ... NOT OFFICIAL`, `.test` URLs, and `official=false`. They exist only to prove the contracts and must never be published as municipal facts.

## Persistence and failure behavior

Migration `0013_municipal_ingestion` creates the source registry, immutable batch evidence, hash-only quarantine, and lineage columns on parking zones and facilities. The migration is reversible. Database constraints enforce enum values, refresh/staleness bounds, official-license presence, batch counts, and source/digest idempotency.

An entirely invalid feed is stored as a rejected batch; a mixed feed is partial; a fully valid feed is committed. Accepted records and batch/quarantine evidence are written within the request transaction. Parser errors do not disclose raw feed content in public responses.

## Configuration

```dotenv
# Keep false until the owner has approved real source rights and staging validation.
PARKSHIELD_MUNICIPAL_IMPORTS_ENABLED=false
PARKSHIELD_MUNICIPAL_MAX_UPLOAD_BYTES=5242880
```

No municipal API key variable exists because the implementation does not perform remote fetching. If a future contracted feed needs authentication, add a separate fetch-provider port, a domain-restricted adapter, a Secrets Manager value, and contract tests before enabling it.

## Verification gates

The phase gate includes Ruff, MyPy, Bandit, the complete backend test suite with the unchanged 90% minimum, migration head/offline generation, a real PostgreSQL/PostGIS migration and repository test in hosted CI, repository policy, secret scanning, container/Compose gates, and unchanged Flutter/native gates. Exact commit and hosted results are recorded in the Draft pull request.

## Manual activation checklist for Miami-Dade or Broward

1. Obtain written usage and redistribution rights from the authoritative data owner; record the public license URL and contact.
2. Confirm jurisdiction, official status, update cadence, expected outage behavior, retention, and attribution with legal/product owners.
3. Obtain the real schema and a representative non-sensitive sample through an approved channel.
4. Map every field to one supported contract; extend the connector and its synthetic contract tests if the source differs.
5. Assign a named data-quality owner and alert destination; define freshness and correction SLAs.
6. Validate the sample offline and review all rejected-record reason codes. Do not place source payloads or credentials in Git, logs, tickets, or chat.
7. Register the source in staging with MFA. Set `official=true` only after the authoritative and legal reviews are evidenced.
8. Enable imports only in staging, upload one approved sample, and inspect lineage, geometry, counts, freshness, audit events, quarantine hashes, and map behavior.
9. Exercise replay, partial rejection, rollback, and source outage procedures; document approval evidence.
10. Obtain explicit promotion authorization before configuring production. Terraform apply, provider credentials, production ingestion, and deployment remain blocked.
