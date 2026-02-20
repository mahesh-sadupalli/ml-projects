"""Extract entities and relationships from text using an LLM."""

from __future__ import annotations

import json
import logging

import ollama as ollama_client

from src.config import settings
from src.knowledge_graph.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """\
You are an entity and relationship extractor. Given the following text, extract:
1. **Entities**: Important nouns — people, organizations, systems, policies, concepts, technologies.
2. **Relationships**: How entities relate to each other.

Return ONLY valid JSON in this exact format (no markdown, no explanation):
{{
  "entities": [
    {{"name": "Entity Name", "label": "Category"}}
  ],
  "relationships": [
    {{"from": "Entity A", "to": "Entity B", "type": "RELATES_TO"}}
  ]
}}

Use these labels for entities: Person, Organization, Policy, System, Technology, Concept, Process, Document.
Use these relationship types: RELATES_TO, PART_OF, GOVERNS, USES, DEPENDS_ON, DEFINES, MENTIONS.

Text:
{text}
"""


def extract_entities_and_relations(text: str) -> dict:
    """Use the LLM to extract entities and relationships from text.

    Returns a dict with "entities" and "relationships" lists.
    Falls back to empty lists on parse failure.
    """
    prompt = EXTRACTION_PROMPT.format(text=text[:3000])  # Limit input size

    response = ollama_client.chat(
        model=settings.ollama_model,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.0},
    )

    content = response["message"]["content"].strip()

    # Try to extract JSON from the response
    try:
        # Handle case where LLM wraps JSON in markdown code block
        if "```" in content:
            start = content.index("{")
            end = content.rindex("}") + 1
            content = content[start:end]
        return json.loads(content)
    except (json.JSONDecodeError, ValueError):
        logger.warning("Failed to parse LLM extraction output, returning empty result")
        return {"entities": [], "relationships": []}


def extract_and_store(text: str, metadata: dict, neo4j: Neo4jClient) -> int:
    """Extract entities/relations from text and store them in Neo4j.

    Also creates a Document node linked to extracted entities.
    Returns the number of entities created.
    """
    result = extract_entities_and_relations(text)

    entities = result.get("entities", [])
    relationships = result.get("relationships", [])

    # Create a document node
    source = metadata.get("source", "unknown")
    neo4j.create_entity("Document", source, {"type": metadata.get("type", "unknown")})

    # Create entity nodes
    for entity in entities:
        name = entity.get("name", "").strip()
        label = entity.get("label", "Concept").strip()
        if name:
            neo4j.create_entity(label, name)
            neo4j.create_relationship("Document", source, label, name, "MENTIONS")

    # Create relationships
    for rel in relationships:
        from_name = rel.get("from", "").strip()
        to_name = rel.get("to", "").strip()
        rel_type = rel.get("type", "RELATES_TO").strip().replace(" ", "_")
        if from_name and to_name:
            neo4j.create_relationship("Concept", from_name, "Concept", to_name, rel_type)

    logger.info("Extracted %d entities, %d relationships from %s", len(entities), len(relationships), source)
    return len(entities)
