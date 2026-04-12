import logging

from fastapi import APIRouter, Request

from src.agents.orchestrator import run_agent
from src.api.models import QueryRequest, QueryResponse, SourceInfo
from src.rag.generator import generate_answer

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
def query_documents(request: QueryRequest, http_request: Request) -> QueryResponse:
    chroma = http_request.app.state.chroma
    neo4j = http_request.app.state.neo4j

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
