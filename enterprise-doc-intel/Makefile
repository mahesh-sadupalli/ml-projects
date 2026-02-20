.PHONY: setup serve ingest query clean test

setup:
	docker compose up -d
	ollama pull llama3.2
	ollama pull nomic-embed-text
	pip install -e ".[dev]"

serve:
	uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000

ingest:
	python -m src.ingestion.pipeline

query:
	@read -p "Question: " q; \
	curl -s -X POST http://localhost:8000/query \
		-H "Content-Type: application/json" \
		-d "{\"question\": \"$$q\"}" | python -m json.tool

clean:
	rm -rf chroma_data
	docker compose down -v

test:
	pytest -v
