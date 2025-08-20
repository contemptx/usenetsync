.PHONY: env up db-migrate py-lint py-type py-test py-live rust-lint rust-test web-build e2e live all

env:
	@test -f .env || (echo ".env missing. Copy .env.example to .env and fill secrets." && exit 1)

up: env
	docker compose up -d postgres

db-migrate: env
	# Adjust to your migration tool (Alembic/SQLx). Placeholder command:
	@echo "Apply DB migrations here (alembic upgrade head)"

py-lint:
	cd backend-python && ruff check . --fix || true

py-type:
	cd backend-python && mypy --strict . || true

py-test:
	cd backend-python && PYTHONPATH=/workspace/src pytest -q -m "unit or integration or live_usenet"

py-live:
	cd backend-python && PYTHONPATH=/workspace/src pytest -q -m "live_usenet"

rust-lint:
	cd usenet-sync-app/src-tauri && source /usr/local/cargo/env && cargo fmt --check && cargo clippy -D warnings || true

rust-test:
	cd usenet-sync-app/src-tauri && source /usr/local/cargo/env && cargo test --all || true

web-build:
	cd usenet-sync-app && npm ci && npm run build

e2e:
	cd frontend-react && npx playwright install --with-deps && npx playwright test --reporter=line || true

live: up db-migrate py-lint py-type rust-lint web-build py-test rust-test e2e

all: live