"""CompletionProvider protocol — the LLM abstraction layer."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class CompletionProvider(Protocol):
    """One-method protocol for LLM calls.

    Applications wrap their LLM client to conform:
    - Atlas wraps Claude
    - Selah wraps Gemma 4
    - Tests use StaticCompletionProvider
    """

    def complete(self, prompt: str, system: str | None = None) -> str: ...


class StaticCompletionProvider:
    """Returns canned responses for testing.

    Matches prompt substrings to responses. Returns default if no match.
    """

    def __init__(
        self,
        responses: dict[str, str] | None = None,
        default: str = "Static summary of the session.",
    ) -> None:
        self._responses = responses or {}
        self._default = default

    def complete(self, prompt: str, system: str | None = None) -> str:
        for key, response in self._responses.items():
            if key in prompt:
                return response
        return self._default
