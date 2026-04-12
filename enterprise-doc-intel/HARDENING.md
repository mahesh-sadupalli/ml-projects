# Phase II Hardening — Issue Tracker

Tracking all issues found and fixed during the Phase II hardening pass.

---

## Issues Fixed

### 1. Path traversal vulnerability in `/ingest` endpoint
- **File:** `src/api/routes/ingest.py`
- **Severity:** High (Security)
- **Problem:** `IngestRequest.data_dir` accepted any string with no validation. A caller could pass `"/"`, `"../../etc"`, or any arbitrary path to read files from the server filesystem.
- **Fix:** Resolve the path and check `is_relative_to(./data/)` before proceeding. Return 400 if the path escapes the allowed root or doesn't exist.

### 2. Neo4j connection leak in ingestion pipeline
- **File:** `src/ingestion/pipeline.py`
- **Severity:** High (Resource leak)
- **Problem:** `neo4j.close()` was only called on the happy path. If `extract_and_store` raised mid-loop, the driver was leaked.
- **Fix:** Move `neo4j.close()` into a `finally` block so the driver is always cleaned up.

### 3. All Ollama calls unguarded
- **Files:** `embeddings/provider.py`, `rag/generator.py`, `knowledge_graph/extractor.py`, `agents/planner.py`, `agents/tools.py`, `agents/orchestrator.py`
- **Severity:** High (Error handling)
- **Problem:** Every Ollama HTTP call (embedding, generation, extraction, planning, summarization, synthesis) had zero try/except. A network failure crashed the entire request with an uncontrolled 500 and raw traceback.
- **Fix:** Wrap all call sites. `provider.py` raises a typed `EmbeddingError`. `generator.py` raises `RuntimeError` with context. `extractor.py`/`planner.py` degrade to empty/fallback results. `tools.py` returns a user-friendly message. `orchestrator.py` returns a fallback answer on synthesis failure and sanitizes tool error messages to avoid leaking internals.

### 4. Graph search traceback swallowed
- **File:** `src/rag/retriever.py:49`
- **Severity:** Medium (Observability)
- **Problem:** `logger.warning` was used instead of `logger.exception`, so graph search tracebacks were completely lost in logs.
- **Fix:** Changed to `logger.exception` to preserve the full traceback.

### 5. ChromaDB query on empty collection
- **File:** `src/vectorstore/chroma.py`
- **Severity:** Medium (Error handling)
- **Problem:** Querying with `top_k` > collection size caused `chromadb.errors.InvalidArgumentError`. Empty collections had no guard.
- **Fix:** Check `collection.count()` before querying. Clamp `top_k` to collection size. Return empty list for empty collections.

### 6. `max_hops` unconstrained for `/graph/neighbors`
- **File:** `src/api/routes/graph.py`
- **Severity:** Medium (Input validation)
- **Problem:** No `ge`/`le` constraint on `max_hops`. A caller could pass `max_hops=1000` triggering an expensive unbounded graph traversal.
- **Fix:** Add `Query(ge=1, le=4)` constraint, matching the `/subgraph` endpoint.

### 7. Graph context heading fused with content
- **Files:** `src/rag/context_builder.py`, `src/knowledge_graph/query.py`
- **Severity:** Medium (Bug)
- **Problem:** `context_builder.py` wrapped graph context in `f"## {graph_context}"` but `query.py` already prepended `"Knowledge Graph Context:\n"`, producing a broken Markdown heading.
- **Fix:** Moved heading responsibility to `context_builder.py` (`## Knowledge Graph Context\n`), removed redundant prefix from `query.py`.

### 8. `compare_documents` dropped Neo4j context
- **File:** `src/agents/tools.py`
- **Severity:** Medium (Bug)
- **Problem:** `compare_documents` called `retrieve(query, chroma, top_k=6)` without passing `neo4j`, unlike `search_documents`. This meant comparison results never included graph-enriched context.
- **Fix:** Added `neo4j` parameter and passed it through in `build_tools`.

### 9. Agent error observations leaked internals
- **File:** `src/agents/orchestrator.py`
- **Severity:** Medium (Security)
- **Problem:** `f"Error: {e}"` in tool error handling could expose file paths, database credentials, or stack details in agent step output returned to the client.
- **Fix:** Use a generic error message `"Error: tool '{tool_name}' failed to execute."` and log the full exception via `logger.exception`.

### 10. New ChromaDB + Neo4j client per request (concurrency)
- **Files:** `src/api/app.py`, `src/api/routes/query.py`, `src/api/routes/health.py`, `src/api/routes/graph.py`
- **Severity:** High (Concurrency)
- **Problem:** Every HTTP request instantiated fresh `ChromaStore()` and `Neo4jClient()`. Under concurrent load, multiple `PersistentClient` instances hitting the same SQLite file caused `database is locked` errors. The Neo4j driver was also being created/destroyed per-request instead of using its built-in connection pool.
- **Fix:** Introduced FastAPI `lifespan` context manager in `app.py`. Shared `chroma` and `neo4j` instances are created at startup and cleaned up at shutdown. All routes now access them via `request.app.state`.

### 11. Test coverage: stub tests replaced with 28 real tests
- **Files:** `tests/test_retriever.py`, `tests/test_knowledge_graph.py`, `tests/test_agent.py`
- **Problem:** All three files were entirely `@pytest.mark.skip` with empty methods — zero executed coverage.
- **Fix:** Replaced with 28 working unit tests using mocked Ollama/Neo4j/ChromaDB covering retriever (vector-only, hybrid, graph failure, empty), KG extraction (valid JSON, markdown-wrapped, bad JSON, empty text, Ollama failure, store creation, entity matching, graph context), and agent (planner parsing/fallback, tools, orchestrator flow/unknown tool/synthesis failure).

### 12. New test coverage for previously untested modules
- **Files:** `tests/test_context_builder.py`, `tests/test_generator.py`, `tests/test_embeddings.py`, `tests/test_pipeline.py`
- **Problem:** `context_builder.py`, `generator.py`, `embeddings/provider.py`, and `pipeline.py` had zero test coverage.
- **Fix:** Added 14 new unit tests covering context assembly, prompt building, LLM generation success/failure, embedding success/failure, pipeline end-to-end flow, empty directory, Neo4j unavailability, and driver cleanup on errors.

### 13. Edge case tests for loader, API models, neo4j_client
- **Files:** `tests/test_loader.py`, `tests/test_api_models.py`, `tests/test_neo4j_client_unit.py`
- **Problem:** Missing PDF loading test, permission error handling, subdirectory recursion, API model validation edge cases, and `_safe_identifier` / label fallback coverage.
- **Fix:** Added 14 new tests covering PDF loading, unreadable files, subdirectories, empty question rejection, `top_k` range validation, default values, `_safe_identifier` valid/invalid/character/space handling, and `create_entity`/`create_relationship` fallback behavior.

---

## Issues Identified (Not Yet Fixed)

### Error Handling
- [ ] **No timeout configuration** — Ollama client has no explicit timeout. A slow model inference can hang a FastAPI worker indefinitely.
- [ ] **Silent partial failure in pipeline** — When KG extraction fails, `run_pipeline` returns `{"entities": 0}` with no indication that the step failed. The API presents partial success as full success.

### Input Validation
- [ ] **Empty entity names accepted** — `neo4j_client.py:create_entity` doesn't validate that `name` is non-empty, allowing polluted graph nodes.

### Code Quality
- [ ] **Plaintext default password** — `config.py:13` has `neo4j_password: str = "password"`.

### Retrieval Quality
- [ ] **No context length cap** — `rag/context_builder.py` assembles context with no token budget. With `top_k=20` and large chunks, can exceed smaller model context windows.
- [ ] **Citation integrity not verified** — LLM may hallucinate `[Source 7]` when only 3 sources were provided. No post-processing validates citation markers.
- [ ] **Entity matching is O(N) substring scan** — `knowledge_graph/query.py:41` fetches up to 500 entities and does linear case-insensitive `in` checks. Short names like `"IT"` cause false positives.
- [ ] **Planner has no few-shot examples** — `agents/planner.py` uses zero-shot prompting. Local LLMs frequently fail to produce valid JSON, silently degrading to single-step search.
- [ ] **`summarize` tool receives query string, not content** — The planner passes a search query to the summarize tool, not actual document text. No tool-chaining mechanism exists.
- [ ] **Agent synthesis has no citation format** — Unlike RAG mode, agent mode has no structured `[Source N]` notation in the synthesis prompt.

### Test Coverage (Remaining)
- [ ] **No tests for API routes** — route handlers (ingest, query, health, graph) have no HTTP-level tests.
- [ ] **No tests for UI dashboard** — `src/ui/dashboard.py` is untested.
- [ ] **Chunker edge cases** — recursive overlap carry-forward and no-separator fallback paths are untested.

---

## Summary

| Metric | Before | After |
|:---|:---|:---|
| Tests passing | 23 (12 skipped) | 79 |
| Test files | 7 (3 stubs) | 11 (all real) |
| Modules with zero test coverage | 11 | 4 |
| Unguarded Ollama calls | 7 | 0 |
| Resource leaks | 2 | 0 |
| Security vulnerabilities | 2 | 0 |
| Per-request client instantiation | Yes | No (lifespan-managed) |
