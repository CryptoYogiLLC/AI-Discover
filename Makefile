# Makefile for AI-Discover project

.PHONY: help setup lint format test fix-all quick-check clean

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Setup development environment
	@chmod +x scripts/setup-dev.sh
	@./scripts/setup-dev.sh

lint: ## Run all linters
	@echo "🔍 Running linters..."
	@cd backend && black --check . && ruff check .
	@cd frontend && npm run lint

format: ## Format all code
	@echo "✨ Formatting code..."
	@cd backend && black . && ruff check --fix .
	@cd frontend && npm run prettier

test: ## Run all tests
	@echo "🧪 Running tests..."
	@cd backend && pytest
	@cd frontend && npm test

fix-all: format ## Fix all auto-fixable issues
	@echo "🔧 Fixing all issues..."
	@pre-commit run --all-files || true
	@make format

quick-check: ## Run quick checks before commit
	@echo "⚡ Running quick checks..."
	@pre-commit run --all-files

clean: ## Clean all generated files
	@echo "🧹 Cleaning..."
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@find . -type d -name ".mypy_cache" -exec rm -rf {} +
	@find . -type d -name ".ruff_cache" -exec rm -rf {} +
	@cd frontend && rm -rf .next node_modules

# Specific fixes for common issues
fix-black: ## Fix Black formatting issues
	@cd backend && black .

fix-ruff: ## Fix Ruff linting issues
	@cd backend && ruff check --fix .

fix-prettier: ## Fix Prettier formatting issues
	@cd frontend && npm run prettier

fix-eslint: ## Fix ESLint issues
	@cd frontend && npm run lint:fix
