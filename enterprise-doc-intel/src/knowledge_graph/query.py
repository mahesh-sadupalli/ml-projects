"""Cypher query builder for knowledge graph context retrieval."""

from __future__ import annotations

from src.knowledge_graph.neo4j_client import Neo4jClient


def get_graph_context(query_entities: list[str], neo4j: Neo4jClient, max_hops: int = 2) -> str:
    """Build a textual context from the knowledge graph for given entities.

    Looks up each entity in the graph, finds neighbors within max_hops,
    and formats the result as natural language context.
    """
    context_parts: list[str] = []

    for entity_name in query_entities:
        # Search for the entity
        matches = neo4j.search_entities(entity_name, limit=3)
        if not matches:
            continue

        for match in matches:
            name = match["name"]
            neighbors = neo4j.get_neighbors(name, max_hops=max_hops)

            if neighbors:
                related = [f"{n['name']} ({', '.join(n['labels'])})" for n in neighbors[:10]]
                context_parts.append(f"'{name}' is related to: {', '.join(related)}")

    if not context_parts:
        return ""

    return "Knowledge Graph Context:\n" + "\n".join(context_parts)


def extract_entities_from_query(query: str, neo4j: Neo4jClient) -> list[str]:
    """Find which entities from the knowledge graph are mentioned in the query.

    Simple keyword matching against known entity names.
    """
    all_entities = neo4j.get_all_entities(limit=500)
    query_lower = query.lower()

    found = []
    for entity in all_entities:
        name = entity["name"]
        if name.lower() in query_lower:
            found.append(name)

    return found
