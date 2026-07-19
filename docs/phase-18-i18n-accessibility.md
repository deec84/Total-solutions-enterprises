# Phase 18 — internationalization and accessibility

## Delivered boundary

The Flutter application resolves English (`en`) and Spanish (`es`) from the operating-system locale, with English as the safe fallback. All 243 maintained first-party message keys live in ARB catalogs and are compiled by Flutter `gen-l10n`; generated Dart files are committed so clean builds are reproducible and a CI drift check rejects stale output.

The localized surface includes authentication and recovery, navigation, administration and MFA, alerts, community reporting, map controls and risk legend, Parking Assistant labels, sign scanner, towing recovery, recommendations, privacy rights, and membership. Dates and US-dollar amounts use the active locale. Stable API and domain values remain separate from presentation strings.

Trust labels have explicit translations for Official Data, AI Prediction, Community Verified, and Estimated. Known parking-risk values are also translated. Unknown future machine values are humanized and displayed rather than hidden or assigned a stronger trust label.

## Content integrity rule

Municipal text, community descriptions, provider records, detected sign text, AI answers/reasons, disclaimers returned by the API, addresses, company names, documents, and payment-method values retain their source content and provenance. ParkShield does not silently machine-translate that material and does not claim that translated or synthetic content is official. A future content-translation provider requires its own consent, quality, privacy, cost, provenance, and fallback review.

## Native configuration

- iOS declares `en` and `es`, embeds localized `InfoPlist.strings`, and supplies localized camera, selected-photo, foreground-location, and explicitly enabled background-location purpose text.
- Android uses a localized application-name resource for default and Spanish resources. The release manifest includes the network permission required by the HTTPS API while cleartext remains disabled.
- Native identifiers, signing, provider files, certificates, and store credentials remain placeholders or absent; no signing identity is fabricated.

## Accessibility controls

- Authentication and asynchronous errors use live-region semantics.
- Forms retain autofill, input type, validation, and accessible Material labels.
- The login experience is scrollable and is exercised at 200% text scaling in Spanish.
- Contrast and Android minimum target-size guidelines run for both locales.
- Map risk legend items wrap instead of forcing a single fixed-width row.

## Gates and coverage policy

`scripts/check-mobile-localizations.py` requires exact catalog key parity, both iOS localized privacy files and target membership, the iOS locale declaration, Android localized resources, and release network permission. CI regenerates localization output and fails on a diff.

Generated `lib/l10n/generated/` code is excluded from line-coverage arithmetic because it is derived and contains one accessor per locale/message. The unchanged 75% threshold applies to maintained Flutter source; ARB parity, generation drift, locale lookup, trust-label behavior, native metadata, bilingual widgets, semantics, contrast, target sizes, and 200% scaling are tested separately. The verified result is 1,823/2,279 lines (79.99%) and 53 passing Flutter tests.

## External gates that remain blocked

Production Spanish enablement and store submission still require:

1. Product and legal review of English and Spanish privacy, consent, deletion, billing, safety, and background-location wording.
2. Physical-device VoiceOver and TalkBack journeys, dynamic-type/font-scale evaluation, switch-control review, and remediation evidence.
3. Approved localized App Store and Google Play description, privacy labels/data-safety answers, screenshots, support URLs, and reviewer notes.
4. Accessibility review of the selected production map, push, tow, store, and municipal-provider experiences.

These are approval and account-dependent gates; they are not skipped, simulated as successful, or required for compiling and testing the current source.
