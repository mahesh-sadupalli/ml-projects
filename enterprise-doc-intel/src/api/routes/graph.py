import logging

from fastapi import APIRouter, HTTPException, Query

from src.api.models import EntityResponse, GraphEdgeResponse, GraphNodeResponse, GraphSubgraphResponse, NeighborResponse
from src.knowledge_graph.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/graph")


def _get_neo4j() -> Neo4jClient:
    try:
        return Neo4jClient()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Neo4j not available: {e}")


@router.get("/entities", response_model=list[EntityResponse])
def list_entities(limit: int = 100) -> list[EntityResponse]:
    neo4j = _get_neo4j()
    try:
        entities = neo4j.get_all_entities(limit=limit)
        return [EntityResponse(name=e["name"], labels=e["labels"]) for e in entities]
    finally:
        neo4j.close()


@router.get("/neighbors/{entity}", response_model=list[NeighborResponse])
def get_neighbors(entity: str, max_hops: int = 2) -> list[NeighborResponse]:
    neo4j = _get_neo4j()
    try:
        neighbors = neo4j.get_neighbors(entity, max_hops=max_hops)
        if not neighbors:
            raise HTTPException(status_code=404, detail=f"Entity '{entity}' not found")
        return [NeighborResponse(name=n["name"], labels=n["labels"], distance=n["distance"]) for n in neighbors]
    finally:
        neo4j.close()


@router.get("/subgraph/{entity}", response_model=GraphSubgraphResponse)
def get_subgraph(
    entity: str,
    max_hops: int = Query(default=2, ge=1, le=4),
    node_limit: int = Query(default=200, ge=1, le=1000),
    edge_limit: int = Query(default=400, ge=1, le=2000),
) -> GraphSubgraphResponse:
    neo4j = _get_neo4j()
    try:
        result = neo4j.get_subgraph(
            entity,
            max_hops=max_hops,
            node_limit=node_limit,
            edge_limit=edge_limit,
        )
        if not result["nodes"]:
            raise HTTPException(status_code=404, detail=f"Entity '{entity}' not found")

        return GraphSubgraphResponse(
            nodes=[GraphNodeResponse(**node) for node in result["nodes"]],
            edges=[GraphEdgeResponse(**edge) for edge in result["edges"]],
        )
    finally:
        neo4j.close()
