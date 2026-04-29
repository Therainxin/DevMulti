"""Backward-compatible mock provider import."""

from __future__ import annotations

from devorbit.llm.mock import MockLLMProvider as _MockLLMProvider


class MockLLMProvider(_MockLLMProvider):
    """Compatibility class for the legacy provider package."""

    def complete(self, *, agent_name: str, prompt: str) -> str:
        """Return generated text for older call sites."""

        return self.generate(f"Agent: {agent_name}\n{prompt}")
