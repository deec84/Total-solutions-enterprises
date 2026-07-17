#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPOSITORY_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)

if ! command -v docker >/dev/null 2>&1; then
  printf 'Docker with Compose v2 is required to verify the local stack.\n' >&2
  exit 1
fi

cd "$REPOSITORY_ROOT"
docker compose version >/dev/null
docker compose ps
docker compose exec -T api python -c \
  "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health/ready')"
docker compose exec -T postgres sh -c \
  'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT postgis_version();"'
docker compose exec -T api alembic -c /app/alembic.ini current | grep '(head)'

printf 'API readiness, Alembic head, PostgreSQL, and PostGIS checks passed.\n'
