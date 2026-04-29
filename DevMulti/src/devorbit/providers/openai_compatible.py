"""Backward-compatible imports for OpenAI-compatible providers."""

from __future__ import annotations

from devorbit.llm.openai_compatible import (
    MiMoCompatibleProvider as _MiMoCompatibleProvider,
    OpenAICompatibleProvider as _OpenAICompatibleProvider,
)


class OpenAICompatibleProvider(_OpenAICompatibleProvider):
    """Compatibility class for the legacy provider package."""

    def complete(self, *, agent_name: str, prompt: str) -> str:
        """Return generated text for older call sites."""

        return self.generate(f"Agent: {agent_name}\n{prompt}")


class MiMoCompatibleProvider(_MiMoCompatibleProvider):
    """Compatibility class for future MiMo-compatible endpoints."""

    def complete(self, *, agent_name: str, prompt: str) -> str:
        """Return generated text for older call sites."""

        return self.generate(f"Agent: {agent_name}\n{prompt}")
