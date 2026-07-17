# ParkShield API

FastAPI modular monolith. Python 3.12 is the supported runtime.

```sh
python3.12 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:create_app --factory --reload
```

Run `ruff check .`, `mypy app`, Bandit, pip-audit, and the full pytest suite before committing. The readiness endpoint verifies PostgreSQL and returns 503 when the dependency is unavailable.

Render migrations without a database using `alembic upgrade head --sql`. Apply them with `alembic upgrade head` after setting `PARKSHIELD_DATABASE_URL` to a PostgreSQL/PostGIS instance.

Staging/production configuration fails at startup when database/JWT defaults remain or SMTP/push credentials are missing. Request logs are structured, correlated, and exclude bodies, query strings, headers, and tokens.

The complete variable inventory and approved secret locations are documented in `../docs/environment-variables.md`. Docker Compose setup and native PostGIS instructions are in `../docs/installation.md`.
