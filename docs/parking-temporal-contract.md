# Temporal parking contract readiness

The public v1 parking-decision response may now include an additive temporal
schedule in `evidence.temporal_rules`, plus `jurisdiction` and the
`decision_rule_id` that produced the response. Each rule records local weekdays,
start/end times, an IANA timezone, validity dates, exception dates, special
restrictions, and windows in which it does not apply. Source and import-batch
lineage remain mandatory for official evidence.

No city, jurisdiction, municipal feed, or real endpoint is configured by this
change. All fixture values are synthetic.

## Safety semantics

- A zone with no declared temporal requirement remains a static rule until its
  evidence expires, preserving existing v1 clients.
- A zone that declares a temporal schedule but supplies none, a malformed rule,
  unknown timezone, expired schedule, or period without an applicable rule
  produces `INDETERMINATE`.
- An exception and a non-applicability window remove that rule from evaluation.
- Concurrent applicable rules are resolved conservatively: `DO_NOT_PARK`, then
  `CAUTION`, then `PARK`. A temporal rule never overrides expired or
  non-official evidence.
- Clients render the typed backend outcome and must not evaluate these rules.

## Pilot URL configuration

Android receives a base URL and comma-separated host allowlist from external
Gradle properties. iOS reads equivalent generated Info.plist build settings.
Both default to `https://api.invalid/`, require HTTPS, and reject hosts outside
the supplied allowlist. A future pilot injects values in protected CI/build
configuration; URLs, tokens, and secrets are not committed.
