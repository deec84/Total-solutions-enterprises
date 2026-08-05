# Mobile foundation: Phase 2.1a

## Scope

This foundation establishes contracts, native project boundaries, design semantics, and CI only. It deliberately excludes splash, onboarding, login UI, maps, camera, chat, persistence implementations, and business workflows.

## Contract consumption

`contracts/openapi/parkshield-api.v1.json` is the immutable input for this phase. Fixtures under `contracts/fixtures/` are synthetic: their identifiers, addresses, and tokens do not identify a person or grant access. The Android and iOS error models represent v1 exactly: `version`, `code`, `message`, `correlation_id`, and optional allowlisted `details`.

New mobile code must switch on error `code`, not messages. `details` is suitable only for field association and must never be logged or presented raw. Correlation IDs may be retained for a user-initiated support flow, never for analytics.

## Security and privacy

Access and refresh credentials belong only in platform secure storage adapters introduced with authentication. API base URLs are injected by build configuration; no environment endpoint, secret, certificate, account ID, or production identifier is checked in. Native logs must redact authorization headers, request payloads, tokens, email addresses, and error details.

The foundation declares dependency-inverted network, secure-storage, and non-sensitive cache boundaries without selecting a transport, keychain/keystore adapter, database, or endpoint configuration. Feature state remains presentation-owned and will be introduced only with a tested vertical slice; navigation is likewise deferred until the first user flow.

## Enforced layer direction

For a feature, `presentation` may reference only its own `presentation`, `domain`, and `core`; `data` may reference only its own `data`, `domain`, and `core`; `domain` may reference only its own `domain`; and `core` may reference only `core`. The architecture guard rejects Kotlin package references and Swift feature-module or feature-path references that cross those boundaries. This preserves the inward direction and prevents presentation from reaching data directly.

## Testing strategy

Native unit tests validate error decoding, design-token mapping, and layer boundaries. Repository checks validate fixture safety, snapshot presence, and source-tree rules. CI compiles Android debug and iOS simulator targets without signing. Integration tests will be added with the first networking vertical after deterministic endpoint configuration exists.
