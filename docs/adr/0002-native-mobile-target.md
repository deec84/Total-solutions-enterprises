# ADR 0002: Native mobile target and Flutter transition

- Status: accepted target; migration not started
- Decision date: 2026-08-01
- Owners required for implementation: product, Android, iOS, backend, security, privacy, accessibility, and release engineering

## Context

ParkShield currently has a tested Flutter client in `mobile/`. It implements the product journeys delivered through Phases 1–19 and remains the only executable mobile client in this repository. The product owner has selected a definitive native architecture: Android with Kotlin and Jetpack Compose, and iOS with Swift and SwiftUI.

This decision does not declare native work complete, re-label Flutter code as native, or authorize deletion of the current client. It establishes a controlled migration that avoids rewriting server-authoritative safety, identity, privacy, billing, provenance, and entitlement rules on each device.

## Decision

Build two independent native presentation clients against the existing versioned REST/OpenAPI boundary:

- Android: Kotlin, Jetpack Compose, ViewModel, coroutines/Flow, platform Keystore, WorkManager, CameraX, location APIs, and platform accessibility semantics.
- iOS: Swift, SwiftUI, structured concurrency, Observation, URLSession, Keychain, BGTaskScheduler, AVFoundation/Vision, Core Location, and platform accessibility semantics.

Each platform owns its UI, navigation, local persistence, permission UX, background execution, device integrations, notification handling, accessibility, and store SDK. Backend responses remain authoritative for parking decisions, provenance, entitlements, moderation, and recovery results. Generated OpenAPI models may be platform-specific; domain policies must not be copied from the backend into clients.

Use shared design tokens, API fixtures, error codes, analytics schemas, accessibility acceptance criteria, and end-to-end journeys. Do not introduce a cross-platform runtime or shared business-logic framework during the first migration. A later shared library requires a separate ADR with measured duplication and lifecycle costs.

## Alternatives considered

### Continue Flutter indefinitely

Advantages: lowest immediate delivery cost, one UI codebase, and existing tests. Disadvantages: it conflicts with the selected native product strategy, complicates first-class platform integrations, and retains a framework dependency for signing, background work, accessibility, camera/location behavior, and store billing.

### Rewrite both native clients at once and remove Flutter

Advantages: fastest theoretical cutover. Disadvantages: creates an unsafe big-bang release, removes the working comparison oracle, duplicates defects across two immature clients, and weakens rollback. Rejected.

### Incremental native vertical slices with Flutter retained

Advantages: measurable parity, reversible rollout, platform-specific quality, and controlled risk. Disadvantages: temporary triple-client maintenance and higher short-term test cost. Selected because ParkShield is a safety-oriented product and rollback matters more than migration speed.

## Current Flutter inventory

The following remain transitional until cutover:

- `mobile/lib`, `mobile/test`, `mobile/android`, `mobile/ios`, localization catalogs, `pubspec.yaml`, and `pubspec.lock`;
- `mobile` and `ios-build` jobs in `.github/workflows/quality.yml`;
- `.github/workflows/mobile-release.yml` and the `mobile-production` environment;
- `scripts/check-flutter-coverage.sh`, localization validation, Flutter setup instructions, and historical phase evidence;
- the unchanged 75% maintained-source Flutter line-coverage threshold.

Historical phase documents accurately describe what was implemented at the time. They are not evidence that Kotlin/Compose or Swift/SwiftUI exists.

## Migration sequence and gates

1. Contract stabilization: publish OpenAPI snapshots, error/provenance schemas, synthetic fixtures, authentication refresh behavior, analytics allowlists, and compatibility policy.
2. Native foundations: create separate Android and iOS roots, dependency rules, design tokens, secure storage, HTTP clients, observability adapters, localization, accessibility harnesses, and CI jobs.
3. Safety-critical vertical slice: registration/login, map, Parking Score, “Can I park here?”, provenance, offline/degraded behavior, and location consent.
4. Device vertical slice: sign camera/scanning, background stop detection, preventive alerts, push handling, community evidence, and recovery navigation.
5. Account and commerce slice: privacy rights, deletion/export, MFA, roles, subscriptions, restore, and server-verified entitlement handling.
6. Parity qualification: platform unit/UI/contract tests, unchanged backend gates, accessibility at 200% text, VoiceOver/TalkBack, low-connectivity and permission-denied journeys, performance, battery, privacy, security, and physical-device matrices.
7. Staged cutover: internal distribution, synthetic-data staging, limited pilot, monitored percentage rollout, rollback rehearsal, and store review. Flutter remains releasable until both native clients satisfy the exit criteria and the owner approves retirement.

No migration stage may lower an existing threshold, skip a test, hard-code official claims, introduce real credentials, or infer provider success.

## Manus reference audit

The supplied Manus Flutter material is a design reference only. Useful concepts to carry into native design exploration are the dark trust-oriented palette, fast home decision entry point, map legend and location details, explicit scan progress/error states, conversational explanation layout, and clear call/navigation recovery actions.

The supplied source is not suitable for direct integration. Rejected elements include its tRPC/cookie/Manus-specific backend contract, base64 image transport, hard-coded statistics or safety claims, incomplete authentication and permission lifecycle, dense eight-item navigation, and absence of ParkShield's existing security, provenance, accessibility, localization, coverage, and provider-boundary gates. No supplied source file is copied into the application, and no simulated claim is presented as official data.

## Consequences

- Feature development that is not a security or critical defect fix should be planned against native vertical slices.
- Flutter dependencies and workflows remain security-maintained but are not an architectural expansion target.
- CI cost rises during migration; budgets and runner concurrency require owner approval before native matrices expand.
- Product analytics must distinguish platform/client version without collecting device identifiers or precise location.
- Store bundle identifiers, signing identities, products, and contracts remain external owner-controlled gates.

## Estado de la arquitectura móvil nativa

Android Kotlin/Compose and iOS Swift/SwiftUI are the approved definitive architecture, but neither client has been created. Flutter remains the functional, tested, transitional client. Native production readiness is therefore **blocked**, not completed. The next safe engineering step is a separately reviewed native-foundation proposal and OpenAPI contract snapshot; it must not be mixed into GitHub/AWS hardening.
