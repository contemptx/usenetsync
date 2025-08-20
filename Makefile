# UsenetSync Makefile - Clean Structure
.PHONY: help install backend frontend test clean

# Colors for output
GREEN=\033[0;32m
NC=\033[0m # No Color

help:
	@echo "UsenetSync Development Commands:"
	@echo "  make install   - Install all dependencies"
	@echo "  make backend   - Start backend server"
	@echo "  make frontend  - Start frontend dev server"
	@echo "  make test      - Run all tests"
	@echo "  make clean     - Clean build artifacts"

install:
	@echo "$(GREEN)Installing backend dependencies...$(NC)"
	@cd backend && pip install -r requirements.txt
	@echo "$(GREEN)Installing frontend dependencies...$(NC)"
	@cd frontend && npm install

backend:
	@echo "$(GREEN)Starting backend server...$(NC)"
	@. venv/bin/activate && python start_backend.py

frontend:
	@echo "$(GREEN)Starting frontend dev server...$(NC)"
	@cd frontend && npm run dev

test:
	@echo "$(GREEN)Running backend tests...$(NC)"
	@cd backend && PYTHONPATH=src pytest tests/
	@echo "$(GREEN)Running frontend tests...$(NC)"
	@cd frontend && npm test

clean:
	@echo "$(GREEN)Cleaning build artifacts...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@rm -rf frontend/dist frontend/src-tauri/target
	@rm -rf backend/src/unified.egg-info
	@echo "$(GREEN)Clean complete!$(NC)"

# Database commands
db-up:
	docker-compose up -d postgres

db-down:
	docker-compose down

db-reset:
	docker-compose down -v
	docker-compose up -d postgres

# Development shortcuts
dev: install
	@tmux new-session -d -s usenetsync 'make backend' \; split-window -h 'make frontend' \; attach

.DEFAULT_GOAL := help
