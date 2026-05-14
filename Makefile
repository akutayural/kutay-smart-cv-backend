run:
	uv run uvicorn app.main:app --reload

test:
	uv run pytest

lint:
	uv run ruff check .

eval:
	uv run python -m app.evals.runner

ingest:
	uv run python -m app.ai.rag.ingest

docker:
	docker compose up --build
