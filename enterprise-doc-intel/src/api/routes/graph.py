from fastapi import APIRouter, HTTPException, Query, Request

from src.api.models import EntityResponse, GraphEdgeResponse, GraphNodeResponse, GraphSubgraphResponse, NeighborResponse

router = APIRouter(prefix="/graph")


def _require_neo4j(request: Request):
    neo4j = request.app.state.neo4j
    if neo4j is None:
        raise HTTPException(status_code=503, detail="Neo4j not available")
    return neo4j


@router.get("/entities", response_model=list[EntityResponse])
def list_entities(request: Request, limit: int = 100) -> list[EntityResponse]:
    neo4j = _require_neo4j(request)
    entities = neo4j.get_all_entities(limit=limit)
    return [EntityResponse(name=e["name"], labels=e["labels"]) for e in entities]


@router.get("/neighbors/{entity}", response_model=list[NeighborResponse])
def get_neighbors(request: Request, entity: str, max_hops: int = Query(default=2, ge=1, le=4)) -> list[NeighborResponse]:
    neo4j = _require_neo4j(request)
    neighbors = neo4j.get_neighbors(entity, max_hops=max_hops)
    if not neighbors:
        raise HTTPException(status_code=404, detail=f"Entity '{entity}' not found")
    return [NeighborResponse(name=n["name"], labels=n["labels"], distance=n["distance"]) for n in neighbors]


@router.get("/subgraph/{entity}", response_model=GraphSubgraphResponse)
def get_subgraph(
    request: Request,
    entity: str,
    max_hops: int = Query(default=2, ge=1, le=4),
    node_limit: int = Query(default=200, ge=1, le=1000),
    edge_limit: int = Query(default=400, ge=1, le=2000),
) -> GraphSubgraphResponse:
    neo4j = _require_neo4j(request)
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
