# Parking decision contract v1

`GET /api/v1/parking/decision/evaluate` is the only public contract for a native client
to request an authoritative parking decision. Clients render the returned
decision; they must not calculate a parking outcome from score, zone type,
restriction text, map geometry, or cached evidence.

## Request privacy and validity

The older `GET /api/v1/parking/decision` response remains deprecated and is
preserved only for the Flutter transition reference; it must not be used by new
native clients. The evaluation request requires coordinates, `accuracy_meters`, timezone-aware
`located_at`, and `location_consent`. These values are evaluated in memory and
are neither persisted nor echoed in the response. The current safety boundary
requires foreground consent, a location no older than two minutes, and accuracy
of 20 meters or better. Background location and location history are outside
this contract.

## Public response

Every successful response includes:

- `outcome`: `PARK`, `CAUTION`, `DO_NOT_PARK`, or `INDETERMINATE`.
- `coverage_status`: whether current verified evidence supports the decision.
- safe, machine-readable `reasons`.
- `evaluated_at` and, when evidence exists, provenance, confidence,
  `observed_at`, `expires_at`, and source/import-batch identifiers.

Coordinates, user identity, tokens, source URLs, raw municipal payloads, and
internal rule details are never returned.

## Fail-closed rules

`PARK` is possible only with current `official` evidence at confidence 0.90 or
higher. Private property, a resident-only zone without a declared permit, and
a towing hotspot return `DO_NOT_PARK`. The following always return
`INDETERMINATE`: no verified coverage, expired evidence, non-official or
low-confidence evidence, insufficient GPS precision, stale location, or absent
location consent. `INDETERMINATE` means the application must direct the user to
read current signs; it never means parking is permitted.

This contract currently models evidence freshness through `expires_at`; it does
not model municipal calendar schedules or temporary-rule intervals. Until an
official source supplies that structured schedule data and its evaluation rules
are separately contracted, those conditions cannot justify `PARK` or `CAUTION`.

The documented v1 codes `NO_VERIFIED_COVERAGE`, `STALE_DATA`,
`LOCATION_PRECISION_INSUFFICIENT`, and `DECISION_INDETERMINATE` are used as
safe decision reasons. They are also reserved in the v1 error-code catalog for
future request failures; a client must not infer parking permission from an
HTTP error.

## Data and rollout boundary

Fixtures in `contracts/fixtures/parking/` are synthetic and are not geographic
coverage. No municipal source is enabled by this change. A pilot requires an
approved official source, rights and licence review, field mapping, freshness
policy, data-quality owner, monitored import, and a separate release approval.
