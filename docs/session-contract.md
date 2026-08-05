# Session contract v1

## Credentials

Login and refresh return a `TokenPair` with opaque `access_token` and `refresh_token` values. Clients must not parse, inspect, or depend on their cryptographic representation. `token_type` is `bearer` and `expires_in` is the access-token lifetime in seconds; the configured default is 900 seconds.

The server-configured refresh-token lifetime is 30 days by default. This lifetime is enforced server-side and is intentionally not used by clients to decide whether a stored token is valid.

## Refresh and concurrent use

Every successful refresh consumes the submitted refresh token and issues a new pair. The prior token is unusable immediately after the first success. If the same token is presented concurrently, exactly one request succeeds with `200 TokenPair`; every other request receives `401 SESSION_INVALID`. Clients must serialize refresh work locally and treat all refresh failures as terminal session recovery failures.

## Logout and revocation

Logout accepts a structurally valid refresh-token payload and always responds with `204`, including when the token is expired, revoked, or already consumed. It revokes a valid refresh token immediately. Deleting a session through `/api/v1/auth/sessions/{session_id}` likewise revokes that refresh token immediately.

Neither operation invalidates access tokens already issued. An access token remains usable until `expires_in` elapses, unless normal account authentication fails. Clients must clear their local credentials immediately after logout or a terminal refresh failure.

## Public failures

Invalid credentials, inactive accounts, and unverified accounts return `401 AUTHENTICATION_FAILED`; clients must not infer an account's internal state. Expired, malformed, replayed, or revoked refresh tokens return `401 SESSION_INVALID`. Rate-limited login returns `429 RATE_LIMITED` and may include `Retry-After`.

All API errors use the v1 envelope defined in `docs/api-error-contract.md`. Clients branch on `code`, retain `correlation_id` only for user-initiated support, and never log or display raw token values.
