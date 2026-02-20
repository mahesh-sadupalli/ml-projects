"""Integration test stubs for the agentic system — require Ollama running."""

import pytest


@pytest.mark.skip(reason="Requires Ollama and ChromaDB running locally")
class TestAgent:
    def test_simple_query_uses_single_step(self):
        """A simple question should result in a single search step."""
        pass

    def test_complex_query_decomposes(self):
        """A comparison question should decompose into multiple steps."""
        pass

    def test_agent_produces_answer(self):
        """Agent should return a non-empty answer with reasoning steps."""
        pass
