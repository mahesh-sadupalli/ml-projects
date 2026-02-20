import logging

from fastapi import APIRouter

from src.agents.orchestrator import run_agent
from src.api.models import QueryRequest, QueryResponse, SourceInfo
from src.knowledge_graph.neo4j_client import Neo4jClient
from src.rag.generator import generate_answer
from src.vectorstore.chroma import ChromaStore

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_neo4j() -> Neo4jClient | None:
    try:
        return Neo4jClient()
    except Exception:
        logger.warning("Neo4j not available, proceeding without knowledge graph")
        return None


@router.post("/query", response_model=QueryResponse)
def query_documents(request: QueryRequest) -> QueryResponse:
    chroma = ChromaStore()
    neo4j = _get_neo4j()

    try:
        if request.mode == "agent":
            result = run_agent(request.question, chroma, neo4j)
            return QueryResponse(
                answer=result.answer,
                mode="agent",
                agent_steps=[
                    {
                        "thought": s.thought,
                        "tool": s.tool,
                        "input": s.tool_input,
                        "observation": s.observation[:500],
                    }
                    for s in result.steps
                ],
            )
        else:
            result = generate_answer(request.question, chroma, neo4j, top_k=request.top_k)
            return QueryResponse(
                answer=result.answer,
                mode="rag",
                sources=[SourceInfo(source=s["source"], score=s["score"]) for s in result.sources],
                graph_context=result.graph_context,
            )
    finally:
        if neo4j:
            neo4j.close()
