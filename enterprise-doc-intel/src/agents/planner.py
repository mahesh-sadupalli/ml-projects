"""Query decomposition — breaks complex questions into sub-steps."""

from __future__ import annotations

import json
import logging

import ollama as ollama_client

from src.config import settings

logger = logging.getLogger(__name__)

DECOMPOSITION_PROMPT = """\
You are a query planner. Given a user question, decompose it into a sequence of steps
that an AI agent should follow. Each step should use one of these tools:

Available tools:
{tool_descriptions}

Return ONLY valid JSON (no markdown, no explanation):
{{
  "steps": [
    {{"tool": "tool_name", "input": "what to pass to the tool", "reason": "why this step"}}
  ]
}}

If the question is simple and can be answered with a single search, use just one step.

Question: {question}
"""


def decompose_query(question: str, tool_descriptions: str) -> list[dict]:
    """Decompose a complex question into a sequence of tool-use steps.

    Returns a list of dicts with "tool", "input", and "reason" keys.
    """
    prompt = DECOMPOSITION_PROMPT.format(
        question=question,
        tool_descriptions=tool_descriptions,
    )

    response = ollama_client.chat(
        model=settings.ollama_model,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.0},
    )

    content = response["message"]["content"].strip()

    try:
        if "```" in content:
            start = content.index("{")
            end = content.rindex("}") + 1
            content = content[start:end]
        parsed = json.loads(content)
        return parsed.get("steps", [])
    except (json.JSONDecodeError, ValueError):
        logger.warning("Failed to parse planner output, falling back to single search step")
        return [{"tool": "search_documents", "input": question, "reason": "direct search"}]
