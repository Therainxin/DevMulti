"""Abstract LLM provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Text generation interface consumed by DevOrbit agents."""

    name: str

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate a response for a prompt."""

