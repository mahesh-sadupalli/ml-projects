# Enterprise Document Intelligence

Enterprise Document Intelligence is a local-first AI platform that combines retrieval-augmented generation (RAG), knowledge graphs, and agentic workflows to answer complex questions across internal documents.

## Project Status

**Current stage: Phase I (functional prototype / foundation complete).**

Implemented capabilities:
- End-to-end ingestion pipeline (load, chunk, embed, store)
- Hybrid retrieval (vector + graph context)
- Agent orchestration for multi-step reasoning
- FastAPI service for ingestion, querying, and graph exploration

Not yet production-ready:
- Limited automated integration coverage (most integration tests are stubs)
- No CI/CD, evaluation harness, or monitoring
- Runtime dependencies (Ollama/Neo4j) assumed to be available locally

## Architecture

```text
Documents -> Loader -> Chunker -> Embeddings -> ChromaDB (vector store)
                          \-> LLM Extraction -> Neo4j (knowledge graph)

Query -> Hybrid Retriever (vector + graph) -> Context Builder -> LLM Generator -> Answer
  or
Query -> Agent Planner -> ReAct Tool Loop (search, graph, summarize, compare) -> Answer
```

## Core Modules

| Module | Responsibility |
|---|---|
| `src/ingestion/` | Document loading (PDF, Markdown, TXT) and chunking |
| `src/embeddings/` | Embedding generation through Ollama (`nomic-embed-text`) |
| `src/vectorstore/` | ChromaDB persistence and similarity search |
| `src/knowledge_graph/` | Neo4j client, extraction, and graph queries |
| `src/rag/` | Retrieval, context construction, and answer generation |
| `src/agents/` | Query decomposition and multi-step tool orchestration |
| `src/api/` | FastAPI application and route handlers |

## Technology Stack

- Python 3.11+
- FastAPI
- Ollama (LLM + embeddings)
- ChromaDB
- Neo4j

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health check |
| `POST` | `/ingest` | Ingest documents from a directory |
| `POST` | `/query` | Ask a question (`rag` or `agent`) |
| `GET` | `/graph/entities` | List entities from the knowledge graph |
| `GET` | `/graph/neighbors/{entity}` | List neighbors for a given entity |

## Roadmap

- Phase I (current): from-scratch implementation of RAG + KG + agent workflows
- Phase II: stronger orchestration and workflow control
- Phase III: production hardening (evaluation, observability, CI/CD)
