# ADR 0002: Native mobile foundation

## Status

Accepted for Phase 2.1a.

## Decision

ParkShield ships separate native clients: Android uses Kotlin with Jetpack Compose and iOS uses Swift with SwiftUI. `mobile/` remains an unmodified Flutter reference during the transition and is not a target architecture.

Each client is feature-first and layered: `core` contains platform infrastructure, `feature/*/domain` contains platform-native models and use cases, `feature/*/data` owns REST adapters, and `feature/*/presentation` owns screens and state. Dependencies point inward. No shared mobile runtime, generated client, business workflow, or UI component is introduced.

The checked-in OpenAPI v1 snapshot is the sole REST contract. Both clients map the public `ErrorResponse` envelope by `code`, retain `correlation_id` for support, and never display raw `details`.

## Consequences

Platform design systems translate shared semantic tokens into native Material 3 and SwiftUI values; visual components are intentionally not forced to match. Both clients use async/await-native networking, secure platform credential stores, dependency injection at composition roots, and offline persistence only behind feature-owned ports.

This phase contains no product flow or production signing. Android and iOS CI compile foundation targets without signing, and architecture checks prevent references to Flutter from the native source trees.
