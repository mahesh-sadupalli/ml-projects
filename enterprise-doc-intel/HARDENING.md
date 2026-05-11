# Phase II Hardening — Issue Tracker

All issues identified during Phase II have been resolved.

---

## Issues Fixed

### 1. Path traversal vulnerability in `/ingest` endpoint
- **File:** `src/api/routes/ingest.py`
- **Severity:** High (Security)
- **Fix:** Resolve the path and check `is_relative_to(./data/)` before proceeding. Return 400 if the path escapes the allowed root or doesn't exist.

### 2. Neo4j connection leak in ingestion pipeline
- **File:** `src/ingestion/pipeline.py`
- **Severity:** High (Resource leak)
- **Fix:** Move `neo4j.close()` into a `finally` block so the driver is always cleaned up.

### 3. All Ollama calls unguarded
- **Files:** `embeddings/provider.py`, `rag/generator.py`, `knowledge_graph/extractor.py`, `agents/planner.py`, `agents/tools.py`, `agents/orchestrator.py`
- **Severity:** High (Error handling)
- **Fix:** Wrap all call sites with typed errors or graceful fallbacks. Agent error observations sanitized to avoid leaking internals.

### 4. Graph search traceback swallowed
- **File:** `src/rag/retriever.py`
- **Fix:** Changed `logger.warning` to `logger.exception` to preserve full tracebacks.

### 5. ChromaDB query on empty collection
- **File:** `src/vectorstore/chroma.py`
- **Fix:** Clamp `top_k` to collection size. Return empty list for empty collections.

### 6. `max_hops` unconstrained for `/graph/neighbors`
- **File:** `src/api/routes/graph.py`
- **Fix:** Add `Query(ge=1, le=4)` constraint.

### 7. Graph context heading fused with content
- **Files:** `src/rag/context_builder.py`, `src/knowledge_graph/query.py`
- **Fix:** Proper Markdown heading in context_builder, removed redundant prefix from query.py.

### 8. `compare_documents` dropped Neo4j context
- **File:** `src/agents/tools.py`
- **Fix:** Added `neo4j` parameter and passed it through in `build_tools`.

### 9. Agent error observations leaked internals
- **File:** `src/agents/orchestrator.py`
- **Fix:** Generic error message with full exception logged via `logger.exception`.

### 10. New ChromaDB + Neo4j client per request (concurrency)
- **Files:** `src/api/app.py`, all route files
- **Fix:** FastAPI `lifespan` context manager with shared clients created at startup, cleaned up at shutdown.

### 11. No Ollama timeout configuration
- **Files:** `src/config.py`, all Ollama call sites
- **Fix:** Added `ollama_timeout` setting (default 120s). All modules now use a configured `ollama.Client` instance instead of the module-level default.

### 12. Plaintext default password
- **File:** `src/config.py`
- **Fix:** Changed `neo4j_password` default from `"password"` to `""` (must be set via `.env`).

### 13. No context length cap
- **File:** `src/rag/context_builder.py`
- **Fix:** Added `max_context_chars` setting (default 8000). Context assembly stops adding sources once budget is reached.

### 14. Entity matching false positives
- **File:** `src/knowledge_graph/query.py`
- **Fix:** Skip entity names shorter than 3 characters to avoid matching common words like "IT", "AI".

### 15. Planner had no few-shot examples
- **File:** `src/agents/planner.py`
- **Fix:** Added 2 few-shot examples (simple single-step, multi-step comparison) to improve JSON output reliability.

### 16. `summarize` tool received query string instead of content
- **File:** `src/agents/tools.py`
- **Fix:** Summarize tool now chains `search_documents` → `summarize` so the LLM receives actual document content.

### 17. Agent synthesis had no citation format
- **File:** `src/agents/orchestrator.py`
- **Fix:** Synthesis prompt now instructs LLM to cite sources using `[Source: filename]` notation from file paths in observations.

### 18. Empty entity names accepted
- **File:** `src/knowledge_graph/neo4j_client.py`
- **Fix:** `create_entity` skips empty/whitespace names and strips valid names before storing.

### 19. Silent partial failure in pipeline
- **File:** `src/ingestion/pipeline.py`
- **Fix:** KG extraction failures now surface via `kg_warning` field in the summary dict.

### 20. Test coverage gaps resolved
- Replaced 3 empty stub test files with real unit tests
- Added 5 new test files: `test_context_builder.py`, `test_generator.py`, `test_embeddings.py`, `test_pipeline.py`, `test_api_routes.py`
- Added edge cases to `test_loader.py`, `test_api_models.py`, `test_neo4j_client_unit.py`, `test_chunker.py`

---

## Summary

| Metric | Before | After |
|:---|:---|:---|
| Tests passing | 23 (12 skipped) | 94 |
| Test files | 7 (3 stubs) | 12 (all real) |
| Modules with zero test coverage | 11 | 1 (dashboard) |
| Unguarded Ollama calls | 7 | 0 |
| Ollama timeout | None | 120s configurable |
| Resource leaks | 2 | 0 |
| Security vulnerabilities | 2 | 0 |
| Per-request client instantiation | Yes | No (lifespan-managed) |
| Context length cap | None | 8000 chars configurable |
| Planner few-shot examples | 0 | 2 |
| Agent citation format | None | [Source: filename] |
