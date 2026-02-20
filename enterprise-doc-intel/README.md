# Enterprise Document Intelligence

An intelligent document platform that combines **RAG pipelines**, **Knowledge Graphs**, and **Agentic Workflows** to answer complex questions across enterprise documents — built from scratch without LangChain.

## Architecture

```
Documents → Loader → Chunker → Embeddings → ChromaDB (vector store)
                           ↘ LLM Extraction → Neo4j (knowledge graph)

Query → Hybrid Retriever (vector + graph) → Context Builder → LLM Generator → Answer
  or
Query → Agent Planner → ReAct Loop (tools: search, graph, summarize, compare) → Answer
```

### Components

| Module | Description |
|---|---|
| `src/ingestion/` | Document loading (PDF, Markdown, TXT), chunking (fixed-size, recursive) |
| `src/embeddings/` | Embedding generation via Ollama (`nomic-embed-text`) |
| `src/vectorstore/` | ChromaDB wrapper with cosine similarity search |
| `src/knowledge_graph/` | Neo4j integration, LLM-based entity/relation extraction, Cypher queries |
| `src/rag/` | Hybrid retriever, context builder with source attribution, LLM generator |
| `src/agents/` | ReAct agent with query decomposition, tool use, multi-step reasoning |
| `src/api/` | FastAPI endpoints for ingestion, querying, and graph exploration |

## Tech Stack

- **LLM**: Ollama (Llama 3.2 / Mistral) — runs locally, zero cost
- **Embeddings**: Ollama (`nomic-embed-text`)
- **Vector Store**: ChromaDB
- **Graph Database**: Neo4j (Docker)
- **API**: FastAPI
- **Language**: Python 3.11+

## Quick Start

### Prerequisites
- Python 3.11+
- Docker
- [Ollama](https://ollama.ai)

### Setup
```bash
# Start Neo4j
docker compose up -d

# Pull models
ollama pull llama3.2
ollama pull nomic-embed-text

# Install dependencies
pip install -e ".[dev]"
```

### Run
```bash
# Ingest sample documents
python -m src.ingestion.pipeline

# Start API server
make serve

# Query (RAG mode)
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the remote work policy?"}'

# Query (Agent mode — multi-step reasoning)
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Compare the security and leave policies", "mode": "agent"}'

# Explore knowledge graph
curl http://localhost:8000/graph/entities
```

### Test
```bash
pytest -v
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health check |
| `POST` | `/ingest` | Ingest documents from a directory |
| `POST` | `/query` | Ask a question (mode: `rag` or `agent`) |
| `GET` | `/graph/entities` | List all knowledge graph entities |
| `GET` | `/graph/neighbors/{entity}` | Get related entities |

## Project Roadmap

- **Phase I** (current): From-scratch implementation — RAG, KG, agents without frameworks
- **Phase II**: Enhanced with LangChain/LangGraph for advanced orchestration
- **Phase III**: Production-grade — evaluation suite, monitoring, CI/CD
