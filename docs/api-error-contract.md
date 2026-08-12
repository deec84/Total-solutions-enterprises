# API error contract v1

## Purpose

Every handled ParkShield REST API error returns the same versioned, privacy-safe envelope. Clients must branch on `code`, never on the human-readable `message`.

```json
{
  "version": "1",
  "code": "AUTHENTICATION_FAILED",
  "message": "Authentication failed.",
  "correlation_id": "request-correlation-id",
  "details": [{"field": "password", "code": "MISSING_FIELD"}]
}
```

`details` is optional and only used for validation. It contains allowlisted field names and either `MISSING_FIELD` or `INVALID_FIELD`; it never includes submitted values, validation-library messages, credentials, tokens, personal data, internal names, or stack traces.

## Initial stable codes

| Code | HTTP status | Client action |
|---|---:|---|
| `INVALID_REQUEST` | 400 | Correct request before retrying. |
| `AUTHENTICATION_REQUIRED` | 401 | Obtain an authenticated session. |
| `AUTHENTICATION_FAILED` | 401 | Show generic login failure. |
| `SESSION_INVALID` | 401 | Clear protected session state and reauthenticate. |
| `AUTHORIZATION_DENIED` | 403 | Do not retry without changed authorization. |
| `RESOURCE_NOT_FOUND` | 404 | Treat as absent or stale local state. |
| `CONFLICT` | 409 | Refresh state before retrying. |
| `VALIDATION_FAILED` | 422 | Use safe `details` to highlight fields. |
| `RATE_LIMITED` | 429 | Respect `Retry-After` when present. |
| `UNSUPPORTED_MEDIA_TYPE` | 415 | Select a supported content type. |
| `PAYLOAD_TOO_LARGE` | 413 | Reduce payload size. |
| `SERVICE_UNAVAILABLE` | 503 | Retry with bounded backoff. |
| `INTERNAL_ERROR` | 500 | Show a generic failure and retain `correlation_id` for support. |
| `NO_VERIFIED_COVERAGE` | Decision reason | Render `INDETERMINATE`; do not infer that parking is permitted. |
| `STALE_DATA` | Decision reason | Render `INDETERMINATE`; evidence is not current. |
| `LOCATION_PRECISION_INSUFFICIENT` | Decision reason | Ask for a more accurate foreground location. |
| `DECISION_INDETERMINATE` | Decision reason | Do not reinterpret uncertainty as permission to park. |

## Compatibility and evolution

The v1 field set is additive-only. Existing codes cannot change meaning or HTTP status. New codes require a documented client action, a contract test, OpenAPI documentation, and approval from API and mobile owners. A breaking envelope change requires a new version and a parallel deprecation period covering at least one supported Android and iOS release cycle.

## Android and iOS consumption

Android and iOS will deserialize this envelope into platform-native models. Both clients must preserve the correlation ID for user-support flows, avoid displaying raw `details`, and keep authentication recovery keyed to `code`. Neither client may infer behavior from backend exception text.

## Audit record

Before v1, FastAPI default validation responses and route-level `HTTPException` payloads exposed an implicit `detail` shape and depended on unstable exception text. The v1 global handlers normalize those errors without changing authentication, authorization, rate-limit, or business rules.
