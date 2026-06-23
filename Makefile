.PHONY: check test lint format typecheck frontend-build

lint:
	python -m ruff check .

format:
	python -m ruff format .

typecheck:
	python -m mypy .

test:
	python -m pytest -q

check:
	python -m ruff check .
	python -m ruff format --check .
	python -m mypy .
	python -m pytest -q
	python -m codex_quality_gate check . --fail-on-warning

frontend-build:
	cd frontend && npm run build
