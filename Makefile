.PHONY: install test lint run clean coverage benchmark

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

coverage:
	pytest --cov=app --cov-report=html --cov-report=term-missing

lint:
	black app/ tests/ --check
	ruff check app/ tests/

format:
	black app/ tests/
	ruff check app/ tests/ --fix

typecheck:
	mypy app/

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

benchmark:
	pytest tests/performance/ --benchmark-only -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete

help:
	@echo "Available commands:"
	@echo "  make install      - Install production dependencies"
	@echo "  make install-dev  - Install development dependencies"
	@echo "  make test         - Run all tests"
	@echo "  make coverage     - Run tests with coverage report"
	@echo "  make lint         - Check code quality"
	@echo "  make format       - Format code"
	@echo "  make typecheck    - Run type checking"
	@echo "  make run          - Run development server"
	@echo "  make benchmark    - Run performance benchmarks"
	@echo "  make clean        - Clean temporary files"
