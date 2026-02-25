# Enterprise Document Intelligence

Enterprise Document Intelligence is a local-first platform for enterprise knowledge access. It combines retrieval-augmented generation (RAG), knowledge graphs, and agentic reasoning so teams can ask natural-language questions and get grounded answers from internal documents.

## Current Progress (Right Now)

**Stage: Phase I complete (working prototype), moving into Phase II hardening.**

What is already working:
- End-to-end ingestion pipeline: load documents -> chunk -> embed -> store
- Hybrid retrieval: vector similarity + graph-based context enrichment
- Two query modes: direct RAG and agentic multi-step reasoning
- FastAPI service with ingestion, query, and graph endpoints

What we are doing now:
- Strengthening reliability and error handling across pipeline and query paths
- Expanding integration and end-to-end test coverage
- Improving retrieval quality controls and evaluation discipline
- Preparing the codebase for production-grade observability and CI/CD

## Context and Problem Statement

Enterprise documents are usually spread across policies, reports, technical notes, and operational manuals. Even when search exists, users still face three recurring issues:
- Keyword search misses semantic intent
- Valuable relationships between entities (teams, systems, policies) are implicit and hard to traverse
- Complex questions require multi-step reasoning, not just top-k retrieval

This project addresses that gap by combining:
- Semantic retrieval for relevant evidence
- Structured graph context for relationship-aware answers
- Agent workflows for decomposition of complex tasks

## Why This Project Is Relevant

This architecture is relevant for organizations that need:
- Faster onboarding and internal knowledge discovery
- Better decision support from policy and technical documentation
- Lower operational dependence on manual document lookup
- Explainable responses with explicit source grounding

It is also a practical reference implementation for teams building AI document systems from first principles without heavy orchestration frameworks.

## Project Scope

In scope:
- Document ingestion for TXT, Markdown, and PDF
- Chunking strategies for long-context preparation
- Embedding generation using local models
- Persistent vector indexing and similarity retrieval
- Knowledge graph extraction and traversal
- Query answering through RAG and agentic orchestration
- API-first interface for integration

Out of scope (current phase):
- Multi-tenant security and RBAC
- Formal evaluation dashboards and quality gates
- Distributed scaling and cost optimization
- Full production telemetry and SLO enforcement

## Solution Overview

```text
Ingestion path:
Documents -> Loader -> Chunker -> Embeddings -> ChromaDB
                               \-> LLM Extraction -> Neo4j

Question-answering path:
User Query -> Retriever (vector + graph) -> Context Builder -> LLM Generator -> Response

Agent path:
User Query -> Planner -> Tool Execution Loop -> Synthesized Final Answer
```

## Methodology

The implementation follows a modular and incremental methodology:
- Build each capability as an independent module with clear boundaries
- Prefer explicit data flow over hidden framework abstractions
- Gracefully degrade when optional dependencies (for example Neo4j) are unavailable
- Keep interfaces simple so components can be replaced independently

Design principles used in this codebase:
- Local-first runtime with minimal external service dependency
- Retrieval grounding before generation
- Structured and unstructured retrieval working together
- Clear separation between ingestion, retrieval, generation, and orchestration layers

## Step-by-Step Implementation Approach

### 1. Configuration Layer

Central runtime configuration is defined in `src/config.py` via environment-aware settings:
- Model endpoints and model names (generation + embeddings)
- Storage backends (Chroma path, Neo4j credentials)
- Ingestion defaults (data directory, chunk size, overlap)

This ensures consistent behavior across scripts, APIs, and services.

### 2. Document Ingestion

`src/ingestion/loader.py` handles recursive directory loading and format-specific extraction:
- `.txt` and `.md` are read as UTF-8 text
- `.pdf` is parsed through `pypdf` page extraction
- Metadata is attached for traceability (`source`, `type`, page count for PDFs)

### 3. Chunking Strategy

`src/ingestion/chunker.py` provides two chunking modes:
- Fixed-size chunking with overlap
- Recursive chunking using semantic separators (`\n\n`, `\n`, sentence, word)

Chunk metadata preserves source lineage and chunk index for attribution.

### 4. Embedding Generation

`src/embeddings/provider.py` calls Ollama embedding APIs:
- Batch embedding for ingestion
- Single embedding for query-time retrieval

Embeddings convert text to vector space for semantic similarity search.

### 5. Vector Indexing

`src/vectorstore/chroma.py` wraps ChromaDB:
- Persistent collection initialization
- Upsert of chunk text, embedding vectors, and metadata
- Top-k similarity search with cosine space

This serves as the primary evidence retrieval layer for RAG.

### 6. Knowledge Graph Construction

`src/knowledge_graph/extractor.py` and `src/knowledge_graph/neo4j_client.py` implement:
- LLM-based entity and relationship extraction from document text
- Neo4j node and relationship upserts
- Graph neighbor/entity lookup APIs for downstream retrieval

This complements vector retrieval with relationship-aware context.

### 7. Hybrid Retrieval

`src/rag/retriever.py` combines:
- Vector search from Chroma (always)
- Graph context retrieval from Neo4j (optional/fallback-safe)

Result: query context is enriched by both semantic proximity and graph structure.

### 8. Context Building and Answer Generation

`src/rag/context_builder.py` formats retrieved evidence with source labels.
`src/rag/generator.py`:
- Builds final prompt with context + question
- Calls generation model via Ollama
- Returns answer plus source metadata and graph context

### 9. Agentic Reasoning Workflow

For complex questions, `src/agents/` enables multi-step reasoning:
- `planner.py` decomposes questions into tool-oriented steps
- `tools.py` exposes callable tools (search, summarize, compare, graph query)
- `orchestrator.py` executes planned steps and synthesizes the final response

This supports use cases where one-shot retrieval is not enough.

### 10. API Delivery Layer

`src/api/` provides HTTP endpoints for:
- Health checks
- Ingestion jobs
- Query execution (`rag` or `agent`)
- Knowledge graph exploration

This API layer makes the system consumable by UI clients, workflows, or automation scripts.

## Core Modules

| Module | Responsibility |
|---|---|
| `src/ingestion/` | File loading, metadata extraction, and chunk generation |
| `src/embeddings/` | Embedding model integration and vector creation |
| `src/vectorstore/` | ChromaDB persistence, retrieval, and collection management |
| `src/knowledge_graph/` | Entity/relation extraction and Neo4j graph operations |
| `src/rag/` | Hybrid retrieval, context assembly, and grounded answer generation |
| `src/agents/` | Query planning, tool invocation loop, and synthesis |
| `src/api/` | Public service interface and route orchestration |

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service status with vector-store and graph checks |
| `POST` | `/ingest` | Run ingestion pipeline for a directory |
| `POST` | `/query` | Ask questions in `rag` or `agent` mode |
| `GET` | `/graph/entities` | List graph entities |
| `GET` | `/graph/neighbors/{entity}` | Retrieve related entities by hop distance |

## Technology Stack

- Python 3.11+
- FastAPI
- Ollama (LLM + embeddings)
- ChromaDB
- Neo4j
- PyPDF

## Quality and Testing Status

Current test coverage profile:
- Unit-level tests exist for chunking and loaders
- Integration suites for retriever, graph, and agent are present as stubs
- Full reliability validation still requires live dependency-backed integration tests

Current priority is to close this gap before production hardening.

## Roadmap

- Phase I: from-scratch implementation of RAG + KG + agent workflows (completed)
- Phase II: system hardening, evaluation methodology, and stronger orchestration controls (in progress)
- Phase III: production readiness with CI/CD, observability, and operational safeguards
