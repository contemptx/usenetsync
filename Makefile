.PHONY: env check-env db-up db-migrate test-setup test-live test-integration test-all clean help

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help:
	@echo "$(GREEN)UsenetSync Testing Commands$(NC)"
	@echo "  make check-env       - Verify environment configuration"
	@echo "  make db-up          - Start PostgreSQL database"
	@echo "  make test-setup     - Run setup verification tests"
	@echo "  make test-live      - Run live Newshosting tests"
	@echo "  make test-integration - Run integration tests"
	@echo "  make test-all       - Run all tests"
	@echo "  make clean          - Clean test artifacts"

env:
	@test -f .env || (echo "$(RED).env missing. Copy .env.example and add credentials$(NC)" && exit 1)

check-env: env
	@echo "$(GREEN)Checking UsenetSync environment...$(NC)"
	@grep -q "NNTP_HOST=news.newshosting.com" .env || echo "$(YELLOW)Warning: Not using news.newshosting.com$(NC)"
	@grep -q "NNTP_PORT=563" .env || echo "$(YELLOW)Warning: Not using port 563$(NC)"
	@grep -q "NNTP_USERNAME=contemptx" .env || echo "$(YELLOW)Warning: Different username$(NC)"
	@grep -q "NNTP_PASSWORD=Kia211101#" .env && echo "$(GREEN)✓ Credentials configured$(NC)" || echo "$(RED)✗ Password not set$(NC)"
	@echo "$(GREEN)Environment check complete$(NC)"

db-up: env
	@echo "$(GREEN)Starting PostgreSQL...$(NC)"
	@sudo service postgresql status || sudo service postgresql start
	@echo "$(GREEN)PostgreSQL is running$(NC)"

db-migrate: db-up
	@echo "$(GREEN)Setting up UsenetSync database...$(NC)"
	@cd /workspace && . venv/bin/activate && python -c "\
		from src.unified.core.database import UnifiedDatabase, DatabaseConfig, DatabaseType; \
		from src.unified.core.schema import UnifiedSchema; \
		import os; \
		config = DatabaseConfig( \
			db_type=DatabaseType.POSTGRESQL, \
			pg_host='localhost', \
			pg_port=5432, \
			pg_database='usenetsync', \
			pg_user='usenetsync', \
			pg_password='usenetsync123' \
		); \
		db = UnifiedDatabase(config); \
		schema = UnifiedSchema(db); \
		schema.create_all_tables(); \
		print('✓ Database schema created')"

test-setup: env db-up
	@echo "$(GREEN)Running setup verification...$(NC)"
	@cd /workspace && . venv/bin/activate && ./run_tests.sh tests/test_setup.py -v

test-live: env db-up
	@echo "$(GREEN)Running live Newshosting tests...$(NC)"
	@cd /workspace && . venv/bin/activate && ./run_tests.sh tests/test_usenet_live.py -v -m live_nntp

test-integration: env db-up db-migrate
	@echo "$(GREEN)Running integration tests...$(NC)"
	@cd /workspace && . venv/bin/activate && ./run_tests.sh tests/test_integration.py -v -m integration

test-all: env db-up db-migrate
	@echo "$(GREEN)Running all UsenetSync tests...$(NC)"
	@cd /workspace && . venv/bin/activate && ./run_tests.sh -v

py-lint:
	@echo "$(GREEN)Running Python linter...$(NC)"
	@cd /workspace && . venv/bin/activate && ruff check src/ --fix

py-type:
	@echo "$(GREEN)Running type checker...$(NC)"
	@cd /workspace && . venv/bin/activate && mypy src/ --ignore-missing-imports

rust-check:
	@echo "$(GREEN)Checking Rust code...$(NC)"
	@cd /workspace/usenet-sync-app/src-tauri && . /usr/local/cargo/env && cargo check

rust-test:
	@cd /workspace/usenet-sync-app/src-tauri && . /usr/local/cargo/env && cargo test

web-build:
	@echo "$(GREEN)Building frontend...$(NC)"
	@cd /workspace/usenet-sync-app && npm run build

clean:
	@echo "$(GREEN)Cleaning test artifacts...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)Clean complete$(NC)"

# Main test command
live: check-env db-up db-migrate test-all