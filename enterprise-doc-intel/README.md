# Enterprise Document Intelligence

A local-first platform for enterprise knowledge access that combines retrieval-augmented generation (RAG), knowledge graphs, and agentic reasoning. Teams can ask natural-language questions and get grounded, source-cited answers from internal documents — without sending data to external APIs.

Built from first principles with no orchestration frameworks. Every component — chunking, embedding, retrieval, graph extraction, generation, and agent planning — is implemented explicitly so the data flow is transparent and each part can be understood, tested, or replaced independently.

## Table of Contents

- [Why This Exists](#why-this-exists)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Ingestion Pipeline](#ingestion-pipeline)
- [Query Modes](#query-modes)
- [API Reference](#api-reference)
- [Dashboard UI](#dashboard-ui)
- [Project Structure](#project-structure)
- [How Each Module Works](#how-each-module-works)
- [Testing](#testing)
- [Sample Data](#sample-data)
- [Roadmap](#roadmap)

## Why This Exists

Enterprise documents are spread across policies, reports, technical notes, and operational manuals. Existing search tools fall short in three ways:

1. **Keyword search misses semantic intent.** A search for "time off" won't find a document titled "leave policy" unless the exact words match.
2. **Relationships between entities are implicit.** The connection between a team, the systems it owns, and the policies that govern it lives in people's heads, not in a searchable structure.
3. **Complex questions need multi-step reasoning.** "Compare our data security policy with the remote work policy on device requirements" can't be answered by returning the top-5 most similar chunks.

This project addresses all three by combining semantic vector retrieval, a structured knowledge graph, and an agent that can plan and execute multi-step research workflows.

## Architecture

```
Ingestion path:
                                    ┌──────────────┐
  Documents ──► Loader ──► Chunker ─┤              ├──► Embeddings ──► ChromaDB
      (.txt, .md, .pdf)             │              │
                                    └──────┬───────┘
                                           │
                                    LLM Extraction ──► Neo4j (Knowledge Graph)

Query path (RAG mode):
  User Question ──► Embed Query ──► Vector Search (ChromaDB)  ──┐
                                                                 ├──► Context Builder ──► LLM ──► Answer
                 ──► Entity Match ──► Graph Lookup (Neo4j)   ──┘

Query path (Agent mode):
  User Question ──► Planner (LLM decomposes into steps)
                       │
                       ▼
                 Tool Execution Loop
                 (search, summarize, compare, graph query)
                       │
                       ▼
                 Synthesizer (LLM combines all observations) ──► Answer
```

Every external dependency (Neo4j, Ollama) degrades gracefully. If Neo4j is down, queries still work using vector-only retrieval. The system logs a warning and continues.

## Prerequisites

| Dependency | Purpose | Install |
|---|---|---|
| **Python 3.11+** | Runtime | [python.org](https://www.python.org/downloads/) |
| **Ollama** | Local LLM and embedding inference | [ollama.com](https://ollama.com/) |
| **Docker** | Runs Neo4j (knowledge graph) | [docker.com](https://www.docker.com/) |

Ollama models used:
- `llama3.2` — generation and entity extraction
- `nomic-embed-text` — embedding (768-dimensional vectors)

## Quick Start

### 1. Clone and install

```bash
git clone <repo-url>
cd enterprise-doc-intel
```

The `make setup` command handles everything — starts Neo4j via Docker, pulls Ollama models, and installs the Python package with all dependencies:

```bash
make setup
```

Or do each step manually:

```bash
docker compose up -d               # Start Neo4j (port 7474 for browser, 7687 for Bolt)
ollama pull llama3.2                # Pull generation model
ollama pull nomic-embed-text        # Pull embedding model
pip install -e ".[dev,ui]"          # Install package with dev and UI extras
```

### 2. Ingest documents

Place your documents in `data/sample_docs/` (or any directory), then run:

```bash
make ingest
```

This loads all `.txt`, `.md`, and `.pdf` files, chunks them, generates embeddings, stores vectors in ChromaDB, and extracts entities/relationships into Neo4j.

### 3. Start the API

```bash
make serve
```

The API starts at `http://localhost:8000`. Interactive docs are available at `http://localhost:8000/docs` (Swagger UI).

### 4. Ask a question

Using the Makefile shortcut:

```bash
make query
# Prompts for a question, sends it to the API, and pretty-prints the response
```

Using curl directly:

```bash
# RAG mode (single-pass retrieval + generation)
curl -s -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the data security policy?", "mode": "rag", "top_k": 5}' | python -m json.tool

# Agent mode (multi-step reasoning)
curl -s -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Compare the remote work policy with the data security policy on device requirements", "mode": "agent"}' | python -m json.tool
```

### 5. Launch the dashboard (optional)

```bash
make ui
```

Opens a Streamlit dashboard at `http://localhost:8501` with tabs for querying, graph exploration, and system health.

## Configuration

All settings are managed through environment variables or a `.env` file. The configuration is defined in `src/config.py` using Pydantic Settings.

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API endpoint |
| `OLLAMA_MODEL` | `llama3.2` | Model for generation and entity extraction |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Model for embedding generation |
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j Bolt connection URI |
| `NEO4J_USER` | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | `password` | Neo4j password |
| `CHROMA_PERSIST_DIR` | `./chroma_data` | Directory for ChromaDB persistent storage |
| `CHROMA_COLLECTION` | `enterprise_docs` | ChromaDB collection name |
| `CHUNK_SIZE` | `512` | Target chunk size in characters |
| `CHUNK_OVERLAP` | `64` | Overlap between consecutive chunks in characters |
| `DATA_DIR` | `./data/sample_docs` | Default directory for document ingestion |

Example `.env` file:

```env
OLLAMA_MODEL=llama3.2
NEO4J_PASSWORD=my_secure_password
CHUNK_SIZE=1024
CHUNK_OVERLAP=128
```

## Ingestion Pipeline

The pipeline (`src/ingestion/pipeline.py`) runs four stages sequentially:

### Stage 1: Document Loading

`src/ingestion/loader.py` recursively walks a directory and loads files based on extension:

| Format | Extension | Method |
|---|---|---|
| Plain text | `.txt` | UTF-8 read |
| Markdown | `.md` | UTF-8 read |
| PDF | `.pdf` | Page-by-page extraction via `pypdf`, joined with double newlines |

Each loaded document carries metadata: `source` (file path), `type` (text/markdown/pdf), and `pages` (for PDFs).

### Stage 2: Chunking

`src/ingestion/chunker.py` provides two strategies:

**Fixed-size chunking** — Splits text into character windows of `chunk_size` with `overlap` characters shared between consecutive chunks. Simple and predictable.

**Recursive chunking** (default) — Attempts to split on the most meaningful boundary first, falling back to less meaningful ones:
1. Paragraph breaks (`\n\n`)
2. Line breaks (`\n`)
3. Sentence boundaries (`. `)
4. Word boundaries (` `)

If the text fits within `chunk_size`, it becomes a single chunk. Otherwise, the algorithm splits on the best available separator, merges small fragments back together, and preserves `overlap` characters between chunks for context continuity.

Every chunk carries its source lineage (`source`, `chunk_index`, `strategy`).

### Stage 3: Embedding and Vector Storage

`src/embeddings/provider.py` calls Ollama's embedding API for each chunk using `nomic-embed-text`. Embeddings are stored in ChromaDB (`src/vectorstore/chroma.py`) alongside the chunk text and metadata.

ChromaDB is configured with:
- **Cosine distance** metric (HNSW index with `hnsw:space = cosine`)
- **Persistent storage** at `./chroma_data/`
- **Upsert semantics** — re-ingesting the same document updates rather than duplicates (chunk IDs are deterministic SHA-1 hashes of source + index + content)

### Stage 4: Knowledge Graph Extraction

`src/knowledge_graph/extractor.py` sends each document's text (first 3,000 characters) to the LLM with a structured extraction prompt. The LLM returns JSON with:
- **Entities**: named concepts with category labels (Person, Organization, Policy, System, Technology, Concept, Process, Document)
- **Relationships**: directed edges between entities (RELATES_TO, PART_OF, GOVERNS, USES, DEPENDS_ON, DEFINES, MENTIONS)

`src/knowledge_graph/neo4j_client.py` writes these into Neo4j using `MERGE` operations (idempotent — safe to re-run). A Document node is created for each source file and linked to its extracted entities via `MENTIONS` edges.

The Neo4j client validates all labels and relationship types against allowlists before interpolating them into Cypher queries, preventing injection through LLM-generated content.

If Neo4j is unavailable, the pipeline logs a warning and completes without graph extraction.

## Query Modes

### RAG Mode (`mode: "rag"`)

Single-pass retrieval-augmented generation:

1. **Embed the query** — converts the question to a vector using `nomic-embed-text`
2. **Vector search** — finds the top-k most similar chunks in ChromaDB by cosine similarity
3. **Graph enrichment** (if Neo4j available) — identifies entities mentioned in the query, looks up their graph neighbors, and formats relationship context as natural language
4. **Context assembly** — formats retrieved chunks with source labels (`[Source 1: path/to/doc (relevance: 0.847)]`) and appends graph context
5. **Generation** — sends the assembled context + question to `llama3.2` with instructions to cite sources using `[Source N]` notation

The response includes the answer, a list of sources with relevance scores, and any graph context used.

### Agent Mode (`mode: "agent"`)

Multi-step reasoning using a ReAct-style (Reason → Act → Observe) agent:

1. **Planning** — The LLM decomposes the question into a sequence of tool-use steps (up to 8 steps max)
2. **Execution** — Each step invokes one of the available tools:

   | Tool | Description |
   |---|---|
   | `search_documents` | Vector + graph hybrid search, returns top-3 passages with scores |
   | `query_knowledge_graph` | Looks up an entity in Neo4j and returns neighbors within 2 hops |
   | `summarize` | Sends text to the LLM for concise summarization |
   | `compare_documents` | Retrieves documents related to a comparison query, groups by source |

3. **Synthesis** — All step observations are combined and sent to the LLM to produce a final, comprehensive answer

The response includes the answer and the full reasoning trace (thought, tool, input, observation for each step).

Agent mode is useful for questions that require:
- Comparing information across multiple documents
- Following chains of relationships in the knowledge graph
- Summarizing and synthesizing information from several sources

## API Reference

Base URL: `http://localhost:8000`

### `GET /health`

Returns system health with ChromaDB document count and Neo4j connectivity status.

**Response:**
```json
{
  "status": "ok",
  "chroma_docs": 42,
  "neo4j_connected": true
}
```

`status` is `"ok"` when both backends are reachable, `"degraded"` if either is down.

### `POST /ingest`

Runs the ingestion pipeline on a directory.

**Request:**
```json
{
  "data_dir": "./data/sample_docs"
}
```

**Response:**
```json
{
  "documents": 6,
  "chunks": 23,
  "entities": 31
}
```

### `POST /query`

Asks a question against the ingested documents.

**Request:**
```json
{
  "question": "What devices are allowed under the remote work policy?",
  "mode": "rag",
  "top_k": 5
}
```

| Field | Type | Default | Description |
|---|---|---|---|
| `question` | string | (required) | The question to ask (min 1 character) |
| `mode` | `"rag"` \| `"agent"` | `"rag"` | Query strategy |
| `top_k` | integer (1-20) | `5` | Number of chunks to retrieve |

**Response (RAG mode):**
```json
{
  "answer": "According to the remote work policy [Source 1]...",
  "mode": "rag",
  "sources": [
    {"source": "data/sample_docs/policies/remote-work-policy.md", "score": 0.847}
  ],
  "graph_context": "Knowledge Graph Context:\n'Remote Work Policy' is related to: ...",
  "agent_steps": []
}
```

**Response (Agent mode):**
```json
{
  "answer": "Based on my research across multiple documents...",
  "mode": "agent",
  "sources": [],
  "graph_context": "",
  "agent_steps": [
    {
      "thought": "Search for device requirements in policies",
      "tool": "search_documents",
      "input": "device requirements remote work",
      "observation": "[1] (policies/remote-work-policy.md, score=0.823): ..."
    }
  ]
}
```

### `GET /graph/entities`

Lists all entities in the knowledge graph.

**Query parameters:** `limit` (default: 100)

**Response:**
```json
[
  {"name": "Data Security Policy", "labels": ["Policy"]},
  {"name": "Engineering Team", "labels": ["Organization"]}
]
```

### `GET /graph/neighbors/{entity}`

Returns entities within N hops of the given entity.

**Query parameters:** `max_hops` (default: 2)

**Response:**
```json
[
  {"name": "VPN", "labels": ["Technology"], "distance": 1},
  {"name": "IT Department", "labels": ["Organization"], "distance": 2}
]
```

### `GET /graph/subgraph/{entity}`

Returns a full node-edge subgraph around an entity, suitable for graph visualization.

**Query parameters:** `max_hops` (1-4, default: 2), `node_limit` (1-1000, default: 200), `edge_limit` (1-2000, default: 400)

**Response:**
```json
{
  "nodes": [
    {"id": "4:abc123", "name": "Data Security Policy", "labels": ["Policy"]}
  ],
  "edges": [
    {"source": "4:abc123", "target": "4:def456", "type": "GOVERNS"}
  ]
}
```

## Dashboard UI

The Streamlit dashboard (`src/ui/dashboard.py`) provides three tabs:

**Ask tab** — Enter a question, select RAG or Agent mode, adjust top-k, and view the answer with source citations. Agent mode responses show an expandable reasoning trace for each step.

**Graph tab** — Load the entity list from Neo4j, select or type an entity name, configure hop distance and limits, then render an interactive Plotly network graph. Nodes are sized by degree and colored on a blue scale. Hover for entity details.

**System tab** — Check API health, view ChromaDB document count, Neo4j connection status, and preview the first 25 entities in the graph.

Sidebar settings let you change the API base URL, default query mode, and default top-k.

## Project Structure

```
enterprise-doc-intel/
├── src/
│   ├── config.py                      # Central settings (env vars / .env)
│   ├── ingestion/
│   │   ├── loader.py                  # File loading (txt, md, pdf)
│   │   ├── chunker.py                # Fixed-size and recursive chunking
│   │   └── pipeline.py               # End-to-end ingestion orchestration
│   ├── embeddings/
│   │   └── provider.py               # Ollama embedding API wrapper
│   ├── vectorstore/
│   │   └── chroma.py                 # ChromaDB persistence and search
│   ├── knowledge_graph/
│   │   ├── extractor.py              # LLM-based entity/relation extraction
│   │   ├── neo4j_client.py           # Neo4j driver wrapper with Cypher safety
│   │   └── query.py                  # Graph context retrieval for RAG
│   ├── rag/
│   │   ├── retriever.py              # Hybrid vector + graph retrieval
│   │   ├── context_builder.py        # Prompt assembly with source attribution
│   │   └── generator.py              # LLM answer generation with citations
│   ├── agents/
│   │   ├── planner.py                # LLM query decomposition
│   │   ├── tools.py                  # Callable agent tools (search, summarize, compare, graph)
│   │   └── orchestrator.py           # ReAct execution loop and synthesis
│   ├── api/
│   │   ├── app.py                    # FastAPI application entry point
│   │   ├── models.py                 # Pydantic request/response schemas
│   │   └── routes/
│   │       ├── health.py             # GET /health
│   │       ├── ingest.py             # POST /ingest
│   │       ├── query.py              # POST /query
│   │       └── graph.py              # GET /graph/*
│   └── ui/
│       └── dashboard.py              # Streamlit visualization dashboard
├── tests/
│   ├── test_loader.py                # Document loader unit tests
│   ├── test_chunker.py               # Chunking strategy unit tests
│   ├── test_api_models.py            # Pydantic model validation tests
│   ├── test_neo4j_client_unit.py     # Neo4j client unit tests
│   ├── test_retriever.py             # Retriever integration tests
│   ├── test_knowledge_graph.py       # Knowledge graph integration tests
│   └── test_agent.py                 # Agent orchestration tests
├── data/
│   └── sample_docs/                   # Sample enterprise documents
│       ├── policies/                  # HR and security policies
│       ├── reports/                   # Quarterly reports
│       └── technical/                 # Architecture and API docs
├── chroma_data/                       # ChromaDB persistent storage (gitignored)
├── docker-compose.yml                 # Neo4j container definition
├── pyproject.toml                     # Package definition and dependencies
├── Makefile                           # Development shortcuts
└── uv.lock                           # Dependency lock file
```

## How Each Module Works

### Embeddings (`src/embeddings/provider.py`)

Calls Ollama's `/api/embed` endpoint. Two functions:
- `get_embeddings(texts)` — batch embedding for ingestion, iterates over texts one at a time
- `get_single_embedding(text)` — single embedding for query-time retrieval

### Vector Store (`src/vectorstore/chroma.py`)

Wraps `chromadb.PersistentClient` with three operations:
- `add()` — upserts documents with pre-computed embeddings
- `search()` — top-k cosine similarity search, returns results with similarity scores (converts ChromaDB's distance to `1 - distance`)
- `reset()` — drops and recreates the collection

### Knowledge Graph Client (`src/knowledge_graph/neo4j_client.py`)

Thin wrapper around the Neo4j Python driver. All Cypher identifiers (node labels, relationship types) are validated against allowlists before interpolation:
- Allowed labels: Person, Organization, Policy, System, Technology, Concept, Process, Document
- Allowed relationship types: RELATES_TO, PART_OF, GOVERNS, USES, DEPENDS_ON, DEFINES, MENTIONS
- Unrecognized values fall back to `Concept` or `RELATES_TO`

Key operations: `create_entity`, `create_relationship`, `get_neighbors`, `search_entities`, `get_all_entities`, `get_subgraph`.

### Graph Context Retrieval (`src/knowledge_graph/query.py`)

Two-step process used during RAG queries:
1. `extract_entities_from_query()` — case-insensitive keyword match of query text against all known entity names
2. `get_graph_context()` — for each matched entity, finds neighbors within N hops and formats them as natural language context

### Hybrid Retriever (`src/rag/retriever.py`)

Combines vector and graph search:
1. Embeds the query and runs ChromaDB similarity search
2. If Neo4j is available, extracts entities from the query and pulls graph context
3. Returns both in a `RetrievalResult` dataclass

Graph search failures are caught and logged — the system continues with vector-only results.

### Context Builder (`src/rag/context_builder.py`)

Formats retrieval results into a prompt with source attribution:
```
## Retrieved Documents

[Source 1: path/to/doc.md (relevance: 0.847)]
<chunk text>

[Source 2: path/to/other.md (relevance: 0.793)]
<chunk text>

## Knowledge Graph Context:
'Policy X' is related to: Entity A (Label), Entity B (Label)
```

### Generator (`src/rag/generator.py`)

Sends the assembled context + question to Ollama with a system prompt that instructs the LLM to cite sources using `[Source N]` notation. Uses `temperature: 0.1` for focused, deterministic answers.

### Agent Planner (`src/agents/planner.py`)

Sends the user's question to the LLM along with available tool descriptions. The LLM returns a JSON plan:
```json
{"steps": [{"tool": "search_documents", "input": "...", "reason": "..."}]}
```

Falls back to a single `search_documents` step if the LLM output can't be parsed.

### Agent Orchestrator (`src/agents/orchestrator.py`)

Executes the plan step by step (max 8 steps), collects observations, then sends everything to the LLM for synthesis. Returns the final answer with the full reasoning trace.

## Testing

Run the full test suite:

```bash
make test
# or
pytest -v
```

Tests are configured with `pytest-asyncio` in auto mode. The test suite includes:
- Unit tests for chunking logic, document loaders, and API model validation
- Integration test stubs for the retriever, knowledge graph, and agent (these require live Ollama and Neo4j to fully exercise)

## Sample Data

The `data/sample_docs/` directory includes example enterprise documents organized by type:

```
sample_docs/
├── policies/
│   ├── data-security-policy.md
│   ├── leave-policy.md
│   └── remote-work-policy.md
├── reports/
│   └── q4-2024-summary.md
└── technical/
    ├── api-documentation.md
    └── architecture-overview.md
```

These documents demonstrate the system's ability to handle different content types (policies, reports, technical docs) and to extract cross-cutting relationships between entities mentioned across documents.

## Roadmap

| Phase | Focus | Status |
|---|---|---|
| **Phase I** | From-scratch implementation of RAG + knowledge graph + agent workflows | Complete |
| **Phase II** | System hardening, error handling, test coverage, retrieval quality controls | In progress |
| **Phase III** | Production readiness — CI/CD, observability, operational safeguards | Planned |

## Technology Stack

| Component | Technology | Role |
|---|---|---|
| Runtime | Python 3.11+ | Core language |
| API framework | FastAPI + Uvicorn | HTTP service layer |
| LLM inference | Ollama | Local generation and embeddings |
| Vector database | ChromaDB | Persistent similarity search |
| Graph database | Neo4j 5 Community | Entity-relationship storage and traversal |
| PDF parsing | pypdf | PDF text extraction |
| Dashboard | Streamlit | Interactive UI |
| Graph visualization | Plotly + NetworkX | Node-edge rendering |
| Schema validation | Pydantic | Request/response models and settings |
| Package management | setuptools + uv | Build and dependency locking |
