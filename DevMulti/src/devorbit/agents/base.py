"""Base abstractions for DevOrbit agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal

from devorbit.context import AgentContext
from devorbit.llm.provider import LLMProvider
from devorbit.models import AgentStep


class BaseAgent(ABC):
    """Abstract base class for agents that cooperate through ``AgentContext``."""

    name = "base"
    role = "Shared agent foundation"

    def __init__(self, provider: LLMProvider) -> None:
        """Create an agent with a text generation provider."""

        self.provider = provider

    @abstractmethod
    def run(self, context: AgentContext):
        """Execute this agent against the shared context."""

    def log_step(
        self,
        context: AgentContext,
        *,
        action: str,
        prompt: str,
        status: Literal["ok", "warning", "error"] = "ok",
    ) -> AgentStep:
        """Record one provider-backed agent step on the shared context."""

        output = self.provider.generate(prompt)
        step = AgentStep(
            agent_name=self.name,
            role=self.role,
            action=action,
            input_summary=prompt,
            output_summary=output[:240],
            observation=output,
            status=status,
        )
        context.agent_steps.append(step)
        return step

    def trace(self, action: str, prompt: str) -> AgentStep:
        """Compatibility helper for older call sites that do not pass context."""

        context = AgentContext(repo_path=".")
        return self.log_step(context, action=action, prompt=prompt)
