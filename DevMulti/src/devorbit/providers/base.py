"""Backward-compatible provider protocol for model-backed agents."""

from __future__ import annotations

from devorbit.llm.provider import LLMProvider as _LLMProvider


class LLMProvider(_LLMProvider):
    """Compatibility wrapper exposing the old ``complete`` method."""

    def complete(self, *, agent_name: str, prompt: str) -> str:
        """Return generated text for older agent call sites."""

        return self.generate(f"Agent: {agent_name}\n{prompt}")
