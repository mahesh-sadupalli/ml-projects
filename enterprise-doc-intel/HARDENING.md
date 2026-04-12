# Phase II Hardening — Issue Tracker

Tracking all issues found and fixed during the Phase II hardening pass.

---

## Issues Fixed

### 1. Path traversal vulnerability in `/ingest` endpoint
- **File:** `src/api/routes/ingest.py`
- **Severity:** High (Security)
- **Problem:** `IngestRequest.data_dir` accepted any string with no validation. A caller could pass `"/"`, `"../../etc"`, or any arbitrary path to read files from the server filesystem.
- **Fix:** Resolve the path and check `is_relative_to(./data/)` before proceeding. Return 400 if the path escapes the allowed root or doesn't exist.
- **Commit:** `b44fe40`

### 2. Neo4j connection leak in ingestion pipeline
- **File:** `src/ingestion/pipeline.py`
- **Severity:** High (Resource leak)
- **Problem:** `neo4j.close()` was only called on the happy path (line 75). If `extract_and_store` raised mid-loop, the `except Exception` caught it but never closed the driver, leaking a connection pool on every failed ingestion run.
- **Fix:** Move `neo4j.close()` into a `finally` block so the driver is always cleaned up.

---

## Issues Identified (Not Yet Fixed)

### Error Handling
- [ ] **All Ollama calls are unguarded** — `embeddings/provider.py`, `knowledge_graph/extractor.py`, `rag/generator.py`, `agents/planner.py`, `agents/tools.py` make HTTP calls to Ollama with zero try/except. Any network failure crashes the entire request with an uncontrolled 500.
- [ ] **No timeout configuration** — Ollama client has no explicit timeout. A slow model inference can hang a FastAPI worker indefinitely.
- [ ] **ChromaDB query on empty collection** — `vectorstore/chroma.py:search()` doesn't guard against querying when the collection is empty or when `top_k` exceeds document count.
- [ ] **Silent partial failure in pipeline** — When KG extraction fails, `run_pipeline` returns `{"entities": 0}` with no indication that the step failed. The API presents partial success as full success.
- [ ] **Graph search traceback swallowed** — `rag/retriever.py:49` uses `logger.warning` instead of `logger.exception`, so the traceback is lost.

### Input Validation
- [ ] **`max_hops` unconstrained for `/graph/neighbors`** — `api/routes/graph.py:31` has no `ge`/`le` constraint. A caller can pass `max_hops=1000` triggering an expensive graph traversal.
- [ ] **Empty entity names accepted** — `neo4j_client.py:create_entity` doesn't validate that `name` is non-empty, allowing polluted graph nodes.

### Concurrency / Resource Management
- [ ] **New ChromaDB + Neo4j client per request** — `api/routes/query.py` and `health.py` instantiate fresh clients on every HTTP request. Under concurrent load, multiple `PersistentClient` instances hitting the same SQLite file cause `database is locked` errors. Should use shared clients via FastAPI lifespan.
- [ ] **Neo4j driver created per-request** — The `neo4j` Python driver is designed for one-driver-per-app with connection pooling, not per-request construction.

### Code Quality / Bugs
- [ ] **Graph context heading fused with content** — `rag/context_builder.py:27` wraps graph context in `f"## {retrieval.graph_context}"` but the context string already starts with `"Knowledge Graph Context:\n"`, producing broken Markdown.
- [ ] **`compare_documents` drops Neo4j context** — `agents/tools.py:75` calls `retrieve(query, chroma, top_k=6)` without passing `neo4j`, unlike `search_documents`.
- [ ] **Agent error observations leak internals** — `agents/orchestrator.py:85` converts exceptions to `f"Error: {e}"` which can expose file paths or credentials in agent step output returned to the client.
- [ ] **Plaintext default password** — `config.py:13` has `neo4j_password: str = "password"`.

### Retrieval Quality
- [ ] **No context length cap** — `rag/context_builder.py` assembles context with no token budget. With `top_k=20` and large chunks, can exceed smaller model context windows.
- [ ] **Citation integrity not verified** — LLM may hallucinate `[Source 7]` when only 3 sources were provided. No post-processing validates citation markers.
- [ ] **Entity matching is O(N) substring scan** — `knowledge_graph/query.py:41` fetches up to 500 entities and does linear case-insensitive `in` checks. Short names like `"IT"` cause false positives.
- [ ] **Planner has no few-shot examples** — `agents/planner.py` uses zero-shot prompting. Local LLMs frequently fail to produce valid JSON, silently degrading to single-step search.
- [ ] **`summarize` tool receives query string, not content** — The planner passes a search query to the summarize tool, not actual document text. No tool-chaining mechanism exists.
- [ ] **Agent synthesis has no citation format** — Unlike RAG mode, agent mode has no structured `[Source N]` notation in the synthesis prompt.

### Test Coverage
- [ ] **3 test files are empty stubs** — `test_retriever.py`, `test_knowledge_graph.py`, `test_agent.py` are entirely `@pytest.mark.skip` with empty methods.
- [ ] **Zero test coverage for:** `pipeline.py`, `embeddings/provider.py`, `context_builder.py`, `generator.py`, `extractor.py`, `knowledge_graph/query.py`, all API routes, `ui/dashboard.py`.
- [ ] **Missing paths in existing tests:** `test_loader.py` — no PDF test, no permission error, no non-existent dir. `test_chunker.py` — no recursive overlap, no empty input. `test_neo4j_client_unit.py` — no `create_entity`/`create_relationship` fallback tests. `test_api_models.py` — no `IngestRequest` or out-of-range `top_k` tests.
