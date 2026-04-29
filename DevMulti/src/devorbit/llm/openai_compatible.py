"""OpenAI-compatible chat completions provider."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from devorbit.llm.provider import LLMProvider


class OpenAICompatibleProvider(LLMProvider):
    """Provider for OpenAI-compatible chat completions endpoints."""

    name = "openai-compatible"

    def __init__(
        self,
        *,
        endpoint: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        """Initialize provider settings from arguments or environment variables."""

        self.endpoint = endpoint or os.getenv("DEVORBIT_LLM_ENDPOINT", "https://api.openai.com/v1/chat/completions")
        self.api_key = api_key or os.getenv("DEVORBIT_LLM_API_KEY")
        self.model = model or os.getenv("DEVORBIT_LLM_MODEL", "openai-compatible-model")
        self.timeout_seconds = timeout_seconds

    def generate(self, prompt: str) -> str:
        """Call a chat-completions compatible endpoint and return assistant text."""

        if not self.api_key:
            raise RuntimeError(
                "未设置 DEVORBIT_LLM_API_KEY。离线运行请使用 mock Provider；"
                "如需真实调用，请配置 OpenAI-compatible API Key。"
            )

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是 DevOrbit，一个谨慎的代码评审 Agent。请返回简洁、可执行的中文发现和建议。",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"OpenAI-compatible Provider 请求失败，endpoint={self.endpoint!r}，错误：{exc}"
            ) from exc

        try:
            data = json.loads(raw)
            return str(data["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise RuntimeError("OpenAI-compatible Provider 返回了无法识别的响应格式。") from exc


class MiMoCompatibleProvider(OpenAICompatibleProvider):
    """Provider alias for future MiMo-compatible chat completion endpoints."""

    name = "mimo-compatible"

    def __init__(
        self,
        *,
        endpoint: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        """Initialize MiMo-compatible settings from MiMo-specific or generic environment variables."""

        super().__init__(
            endpoint=endpoint or os.getenv("DEVORBIT_MIMO_ENDPOINT"),
            api_key=api_key or os.getenv("DEVORBIT_MIMO_API_KEY"),
            model=model or os.getenv("DEVORBIT_MIMO_MODEL"),
            timeout_seconds=timeout_seconds,
        )
