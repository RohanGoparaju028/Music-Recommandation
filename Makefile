.PHONY: setup data train serve test lint demo
setup:
	uv sync --frozen
data:
	uv run python -m music_ml.cli generate
train: data
	uv run python -m music_ml.cli validate
	uv run python -m music_ml.cli train
serve:
	uv run python -m uvicorn music_ml.api:app --host 127.0.0.1 --port 8000
test:
	uv run python -m pytest --cov=music_ml --cov-report=term-missing --cov-report=xml --cov-fail-under=80
lint:
	uv run ruff check .
	uv run ruff format --check .
demo: setup train
