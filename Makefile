.PHONY: help install install-dev format lint typecheck test test-verbose clean run-example

help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

install: ## Install the package
	uv sync

install-dev: ## Install with development dependencies
	uv sync --dev

format: ## Format code with ruff
	uv run ruff format .

lint: ## Run linting checks
	uv run ruff check .

typecheck: ## Run type checking
	uv run mypy .

test: ## Run tests
	uv run pytest

test-verbose: ## Run tests with verbose output
	uv run pytest -v

check: lint typecheck test ## Run all checks (lint, typecheck, test)

clean: ## Clean up cache files
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete