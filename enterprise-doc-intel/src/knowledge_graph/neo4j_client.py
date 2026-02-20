"""Neo4j driver wrapper for knowledge graph operations."""

from __future__ import annotations

import logging
from typing import Any

from neo4j import GraphDatabase

from src.config import settings

logger = logging.getLogger(__name__)


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
        props = properties or {}
        props["name"] = name
        prop_string = ", ".join(f"e.{k} = ${k}" for k in props)
        cypher = f"MERGE (e:{label} {{name: $name}}) ON CREATE SET {prop_string}"
        self.run_query(cypher, props)

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
        props = properties or {}
        prop_clause = ""
        if props:
            prop_pairs = ", ".join(f"{k}: ${k}" for k in props)
            prop_clause = f" {{{prop_pairs}}}"

        cypher = (
            f"MERGE (a:{from_label} {{name: $from_name}}) "
            f"MERGE (b:{to_label} {{name: $to_name}}) "
            f"MERGE (a)-[r:{rel_type}{prop_clause}]->(b)"
        )
        self.run_query(cypher, {"from_name": from_name, "to_name": to_name, **props})

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

    def clear(self) -> None:
        """Delete all nodes and relationships."""
        self.run_query("MATCH (n) DETACH DELETE n")
