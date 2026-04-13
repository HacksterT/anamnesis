"""OpenAI-compatible completion provider.

Works with any server that speaks the OpenAI chat completions API:
- Ollama  (http://localhost:11434/v1)
- LM Studio (http://localhost:1234/v1)
- vLLM, llama.cpp server, etc.
"""

from __future__ import annotations

import httpx


class OpenAICompatibleProvider:
    """Calls any OpenAI-compatible /chat/completions endpoint."""

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str | None = None,
        timeout: float = 120.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._headers = {"Content-Type": "application/json"}
        if api_key:
            self._headers["Authorization"] = f"Bearer {api_key}"
        self._timeout = timeout

    def complete(self, prompt: str, system: str | None = None) -> str:
        """Send a chat completion request and return the response text."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }

        response = httpx.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers=self._headers,
            timeout=self._timeout,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
