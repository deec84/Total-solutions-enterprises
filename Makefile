.PHONY: help up down logs compose-config verify-stack repository-check backend-test backend-lint mobile-test validate

help:
	@echo "up             Start local stack"
	@echo "down           Stop local stack"
	@echo "logs           Follow local stack logs"
	@echo "compose-config Validate the resolved Compose configuration"
	@echo "verify-stack   Verify API, migration head, PostgreSQL, and PostGIS"
	@echo "repository-check Verify files and exclusions before git init"
	@echo "backend-test   Run backend tests"
	@echo "backend-lint   Run backend lint and type checks"
	@echo "mobile-test    Run Flutter tests"
	@echo "validate       Run every locally executable production gate"

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs --follow

compose-config:
	docker compose config --quiet

verify-stack:
	./scripts/verify-local-stack.sh

repository-check:
	./scripts/check-repository-readiness.sh

backend-test:
	cd backend && python -m pytest

backend-lint:
	cd backend && python -m ruff check . && python -m mypy app

mobile-test:
	cd mobile && flutter test

validate:
	./scripts/run-local-gates.sh
