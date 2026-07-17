# Phase 13 — Parking recommendations

## Delivered

- PostgreSQL/PostGIS parking-facility catalog with meter-based proximity query, GiST index, expiry, price, safety, towing frequency, ratings, availability, provenance, confidence, and data-quality constraints.
- Explainable deterministic ranking: safety 40%, distance 20%, price 15%, historical towing 15%, rating 5%, and availability 5%. Missing data is neutral and disclosed; a user price ceiling excludes unverified/over-budget options.
- Authenticated, non-cacheable nearby API with bounded radius/limit and explicit arrival disclaimer.
- Flutter filters for walking radius and maximum price, ranked cards, reasons, source/confidence, availability, and external navigation.
- PostGIS integration gate creates a real geography point and verifies meter-distance retrieval after migrations.

Municipal/provider ingestion writes only through a separately permissioned data pipeline. The consumer API is read-only, expired records are excluded, and community price observations remain moderated evidence rather than silently overwriting official/provider rows.
