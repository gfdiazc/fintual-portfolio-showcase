.PHONY: help install test lint format clean run benchmark

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	pip install -r requirements.txt
	pip install black ruff mypy pytest pytest-cov pre-commit

install-dev:  ## Install dev dependencies with pre-commit hooks
	pip install -r requirements.txt
	pip install black ruff mypy pytest pytest-cov pre-commit
	pre-commit install

test:  ## Run all tests
	pytest tests/ -v

test-unit:  ## Run unit tests only
	pytest tests/unit/ -v

test-cov:  ## Run tests with coverage report
	pytest tests/unit/ -v --cov=app --cov-report=html --cov-report=term-missing

test-watch:  ## Run tests in watch mode (requires pytest-watch)
	pytest-watch tests/unit/ -v

lint:  ## Run all linters
	black --check app/ tests/
	ruff check app/ tests/
	mypy app/ --ignore-missing-imports

format:  ## Format code with black and ruff
	black app/ tests/ scripts/
	ruff check --fix app/ tests/ scripts/

clean:  ## Clean build artifacts and cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache .coverage htmlcov/ .mypy_cache .ruff_cache dist/ build/

run:  ## Run FastAPI server
	uvicorn app.main:app --reload --port 8000

run-prod:  ## Run FastAPI server in production mode
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

benchmark:  ## Run benchmark comparing strategies
	python scripts/benchmark_strategies.py

benchmark-save:  ## Run benchmark and save results
	python scripts/benchmark_strategies.py | tee docs/benchmarks/latest_run.txt

docker-build:  ## Build Docker image
	docker build -t fintual-portfolio-showcase .

docker-run:  ## Run Docker container
	docker run -p 8000:8000 fintual-portfolio-showcase

docker-test:  ## Run tests in Docker
	docker run --rm fintual-portfolio-showcase pytest tests/unit/ -v

ci-check:  ## Run all CI checks locally
	@echo "Running tests..."
	pytest tests/unit/ -v --cov=app --cov-report=term-missing
	@echo "\nChecking code formatting..."
	black --check app/ tests/
	@echo "\nLinting..."
	ruff check app/ tests/
	@echo "\nType checking..."
	mypy app/ --ignore-missing-imports
	@echo "\n✅ All CI checks passed!"

coverage-report:  ## Generate and open HTML coverage report
	pytest tests/unit/ --cov=app --cov-report=html
	open htmlcov/index.html

setup: install-dev  ## Complete setup (install + hooks)
	@echo "✅ Setup complete! Run 'make help' to see available commands."
