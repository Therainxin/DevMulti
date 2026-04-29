"""Provider factory."""

from __future__ import annotations

from devorbit.llm.mock import MockLLMProvider
from devorbit.llm.openai_compatible import MiMoCompatibleProvider, OpenAICompatibleProvider
from devorbit.llm.provider import LLMProvider
from devorbit.models import ProviderName


def create_provider(name: ProviderName) -> LLMProvider:
    """Create an LLM provider by name."""

    if name == ProviderName.MOCK:
        return MockLLMProvider()
    if name == ProviderName.OPENAI_COMPATIBLE:
        return OpenAICompatibleProvider()
    if name == ProviderName.MIMO_COMPATIBLE:
        return MiMoCompatibleProvider()
    raise ValueError(f"Unsupported provider: {name}")
