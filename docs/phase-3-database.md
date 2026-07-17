# Phase 3: Database

## Implemented foundation

- PostgreSQL 16 with PostGIS 3.4 in the local Compose stack.
- SQLAlchemy 2 async engine and transaction-scoped session factory.
- Alembic configured from the typed application database URL.
- Initial migration for users, refresh sessions, append-oriented audit events, foreign keys, uniqueness, and query indexes.
- PostGIS extension activation in the first migration so geospatial modules share one controlled baseline.
- SQLAlchemy implementations of every identity user/session/audit port.
- Request-scoped FastAPI transactions and database-backed readiness checks.
- Unit repository contracts plus an obligatory CI integration suite against a migrated PostGIS service.
- CI migration rehearsal performs upgrade, downgrade to base, and a second upgrade before tests.

The offline migration render passes and produces transactional PostgreSQL DDL. Local gates currently pass with 26 unit/contract tests and 93.67% coverage. The real PostGIS round-trip and migration rehearsal are configured as required GitHub Actions gates because this host has no Docker runtime.

The next increment adds backup/restore runbooks and exercises identity through the HTTP API against PostgreSQL. Once those gates pass, Phase 3 can close and the interactive map schema/API begins.
