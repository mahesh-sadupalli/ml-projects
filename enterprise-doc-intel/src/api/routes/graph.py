import logging

from fastapi import APIRouter, HTTPException

from src.api.models import EntityResponse, NeighborResponse
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
