"""ReAct-style agent orchestrator: Reason → Act → Observe → Repeat."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import ollama as ollama_client

from src.agents.planner import decompose_query
from src.agents.tools import Tool, build_tools
from src.config import settings
from src.knowledge_graph.neo4j_client import Neo4jClient
from src.vectorstore.chroma import ChromaStore

logger = logging.getLogger(__name__)

MAX_STEPS = 8

SYNTHESIS_PROMPT = """\
You are an intelligent document assistant. Based on the observations collected during research,
provide a comprehensive answer to the user's question. Cite sources where applicable.

Question: {question}

Research steps and observations:
{observations}

Provide a clear, well-structured answer:"""


@dataclass
class AgentStep:
    """A single step in the agent's reasoning chain."""

    thought: str
    tool: str
    tool_input: str
    observation: str


@dataclass
class AgentResult:
    """The final result from the agent, including the reasoning trace."""

    answer: str
    steps: list[AgentStep] = field(default_factory=list)


def run_agent(
    question: str,
    chroma: ChromaStore,
    neo4j: Neo4jClient | None = None,
) -> AgentResult:
    """Run the ReAct agent to answer a complex question.

    1. Plan: Decompose the question into sub-steps.
    2. Execute: Run each step, calling the appropriate tool.
    3. Synthesize: Combine all observations into a final answer.
    """
    tools = build_tools(chroma, neo4j)
    tool_map = {t.name: t for t in tools}
    tool_descriptions = "\n".join(f"- {t.name}: {t.description}" for t in tools)

    # 1. Plan
    plan = decompose_query(question, tool_descriptions)
    logger.info("Agent plan: %d steps", len(plan))

    # 2. Execute steps
    steps: list[AgentStep] = []
    for i, step_plan in enumerate(plan[:MAX_STEPS]):
        tool_name = step_plan.get("tool", "search_documents")
        tool_input = step_plan.get("input", question)
        reason = step_plan.get("reason", "")

        logger.info("Step %d: %s(%s) — %s", i + 1, tool_name, tool_input[:50], reason)

        tool = tool_map.get(tool_name)
        if not tool:
            observation = f"Unknown tool: {tool_name}"
        else:
            try:
                observation = tool.fn(tool_input)
            except Exception as e:
                observation = f"Error: {e}"

        steps.append(
            AgentStep(
                thought=reason,
                tool=tool_name,
                tool_input=tool_input,
                observation=observation[:2000],  # Limit observation size
            )
        )

    # 3. Synthesize
    observations_text = "\n\n".join(
        f"Step {i + 1} ({s.tool}): {s.thought}\nResult: {s.observation}"
        for i, s in enumerate(steps)
    )

    response = ollama_client.chat(
        model=settings.ollama_model,
        messages=[
            {
                "role": "user",
                "content": SYNTHESIS_PROMPT.format(
                    question=question,
                    observations=observations_text,
                ),
            }
        ],
        options={"temperature": 0.1},
    )

    return AgentResult(
        answer=response["message"]["content"],
        steps=steps,
    )
