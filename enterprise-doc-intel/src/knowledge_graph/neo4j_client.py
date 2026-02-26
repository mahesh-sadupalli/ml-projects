"""Neo4j driver wrapper for knowledge graph operations."""

from __future__ import annotations

import logging
import re
from typing import Any

from neo4j import GraphDatabase

from src.config import settings

logger = logging.getLogger(__name__)

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_ALLOWED_LABELS = {
    "Person",
    "Organization",
    "Policy",
    "System",
    "Technology",
    "Concept",
    "Process",
    "Document",
}
_ALLOWED_REL_TYPES = {"RELATES_TO", "PART_OF", "GOVERNS", "USES", "DEPENDS_ON", "DEFINES", "MENTIONS"}


def _safe_identifier(value: str, fallback: str, allowed: set[str] | None = None) -> str:
    candidate = value.strip().replace(" ", "_")
    if allowed and candidate not in allowed:
        return fallback
    if not _IDENTIFIER_RE.fullmatch(candidate):
        return fallback
    return candidate


class Neo4jClient:
    """Thin wrapper around the Neo4j Python driver."""

    def __init__(self) -> None:
        self._driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        self._driver.verify_connectivity()
        logger.info("Connected to Neo4j at %s", settings.neo4j_uri)

    def close(self) -> None:
        self._driver.close()

    def run_query(self, cypher: str, params: dict | None = None) -> list[dict[str, Any]]:
        """Execute a Cypher query and return the results as dicts."""
        with self._driver.session() as session:
            result = session.run(cypher, params or {})
            return [record.data() for record in result]

    def create_entity(self, label: str, name: str, properties: dict | None = None) -> None:
        """Create or merge an entity node."""
        safe_label = _safe_identifier(label, fallback="Concept", allowed=_ALLOWED_LABELS)
        props = properties or {}
        cypher = f"MERGE (e:{safe_label} {{name: $name}}) SET e += $props"
        self.run_query(cypher, {"name": name, "props": props})

    def create_relationship(
        self,
        from_label: str,
        from_name: str,
        to_label: str,
        to_name: str,
        rel_type: str,
        properties: dict | None = None,
    ) -> None:
        """Create a relationship between two entities (creates nodes if missing)."""
        safe_from_label = _safe_identifier(from_label, fallback="Concept", allowed=_ALLOWED_LABELS)
        safe_to_label = _safe_identifier(to_label, fallback="Concept", allowed=_ALLOWED_LABELS)
        safe_rel_type = _safe_identifier(rel_type, fallback="RELATES_TO", allowed=_ALLOWED_REL_TYPES)
        props = properties or {}

        cypher = (
            f"MERGE (a:{safe_from_label} {{name: $from_name}}) "
            f"MERGE (b:{safe_to_label} {{name: $to_name}}) "
            f"MERGE (a)-[r:{safe_rel_type}]->(b) "
            "SET r += $props"
        )
        self.run_query(cypher, {"from_name": from_name, "to_name": to_name, "props": props})

    def get_neighbors(self, name: str, max_hops: int = 2) -> list[dict[str, Any]]:
        """Get all entities within N hops of the given entity."""
        cypher = (
            "MATCH path = (start {name: $name})-[*1.." + str(max_hops) + "]-(neighbor) "
            "RETURN DISTINCT neighbor.name AS name, labels(neighbor) AS labels, "
            "length(path) AS distance "
            "ORDER BY distance"
        )
        return self.run_query(cypher, {"name": name})

    def search_entities(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search entities by name (case-insensitive contains)."""
        cypher = (
            "MATCH (e) WHERE toLower(e.name) CONTAINS toLower($query) "
            "RETURN e.name AS name, labels(e) AS labels "
            "LIMIT $limit"
        )
        return self.run_query(cypher, {"query": query, "limit": limit})

    def get_all_entities(self, limit: int = 100) -> list[dict[str, Any]]:
        """List all entities in the graph."""
        cypher = "MATCH (e) RETURN e.name AS name, labels(e) AS labels LIMIT $limit"
        return self.run_query(cypher, {"limit": limit})

    def get_subgraph(
        self,
        name: str,
        max_hops: int = 2,
        node_limit: int = 200,
        edge_limit: int = 400,
    ) -> dict[str, list[dict[str, Any]]]:
        """Return a node-edge subgraph around an entity."""
        safe_hops = max(1, min(int(max_hops), 4))
        safe_node_limit = max(1, min(int(node_limit), 1000))
        safe_edge_limit = max(1, min(int(edge_limit), 2000))

        start = self.run_query(
            (
                "MATCH (start {name: $name}) "
                "RETURN elementId(start) AS id, coalesce(start.name, elementId(start)) AS name, "
                "labels(start) AS labels "
                "LIMIT 1"
            ),
            {"name": name},
        )
        if not start:
            return {"nodes": [], "edges": []}

        nodes = self.run_query(
            (
                "MATCH path = (start {name: $name})-[*1.."
                + str(safe_hops)
                + "]-(neighbor) "
                "UNWIND nodes(path) AS node "
                "RETURN DISTINCT elementId(node) AS id, "
                "coalesce(node.name, elementId(node)) AS name, "
                "labels(node) AS labels "
                "LIMIT $limit"
            ),
            {"name": name, "limit": safe_node_limit},
        )

        edges = self.run_query(
            (
                "MATCH path = (start {name: $name})-[*1.."
                + str(safe_hops)
                + "]-(neighbor) "
                "UNWIND relationships(path) AS rel "
                "RETURN DISTINCT elementId(startNode(rel)) AS source, "
                "elementId(endNode(rel)) AS target, "
                "type(rel) AS type "
                "LIMIT $limit"
            ),
            {"name": name, "limit": safe_edge_limit},
        )

        if not nodes:
            nodes = [start[0]]
        elif start[0]["id"] not in {node["id"] for node in nodes}:
            nodes.insert(0, start[0])

        return {"nodes": nodes, "edges": edges}

    def clear(self) -> None:
        """Delete all nodes and relationships."""
        self.run_query("MATCH (n) DETACH DELETE n")
