.PHONY: dev test test-pg migrate revision check build up down logs backup restore

dev:        ## API on :8010 with auto-reload (UI: cd frontend && npm run dev)
	cd backend && .venv/bin/uvicorn app.main:app --reload --port 8010

test:       ## backend tests on in-memory SQLite
	cd backend && .venv/bin/pytest -q

test-pg:    ## backend tests on the dev Postgres (docker compose up -d postgres first)
	docker compose exec -T postgres psql -U sl -d postgres -c "DROP DATABASE IF EXISTS semantic_layer_test" -c "CREATE DATABASE semantic_layer_test"
	cd backend && SL_TEST_DATABASE_URL=postgresql://sl:sl@localhost:5432/semantic_layer_test .venv/bin/pytest -q

migrate:    ## apply migrations to the configured database
	cd backend && .venv/bin/python -m app.cli migrate

revision:   ## create a migration after changing models:  make revision m="add foo column"
	cd backend && .venv/bin/alembic revision --autogenerate -m "$(m)"

check:      ## validate config and database state
	cd backend && .venv/bin/python -m app.cli check

build:
	docker compose -f docker-compose.prod.yml build

up:
	docker compose -f docker-compose.prod.yml up -d --build

down:
	docker compose -f docker-compose.prod.yml down

logs:
	docker compose -f docker-compose.prod.yml logs -f --tail=100 app

backup:
	scripts/backup.sh

restore:    ## make restore f=backups/semantic_layer-....dump
	scripts/restore.sh $(f)
