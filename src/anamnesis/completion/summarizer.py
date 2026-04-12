"""Episode summarization orchestrator."""

from __future__ import annotations

from anamnesis.completion.heuristic import HeuristicSummarizer
from anamnesis.completion.prompts import SUMMARIZE_SESSION
from anamnesis.completion.provider import CompletionProvider
from anamnesis.episode.model import Episode
from anamnesis.inject.budget import SimpleTokenCounter, TokenCounter


def summarize_episode(
    episode: Episode,
    budget: int,
    provider: CompletionProvider | None = None,
    counter: TokenCounter | None = None,
) -> str:
    """Summarize an episode within a token budget.

    If a CompletionProvider is given, uses LLM summarization with the
    default prompt template. Otherwise falls back to the heuristic
    summarizer (last N turns, truncated).

    The result is always truncated to fit within the budget, even if
    the provider returns too much.
    """
    if counter is None:
        counter = SimpleTokenCounter()

    if provider is not None:
        return _llm_summarize(episode, budget, provider, counter)

    return HeuristicSummarizer(counter).summarize(episode, budget)


def _llm_summarize(
    episode: Episode,
    budget: int,
    provider: CompletionProvider,
    counter: TokenCounter,
) -> str:
    """Summarize via LLM, with budget enforcement on the output."""
    # Build the turns block
    turns_text = "\n".join(
        f"{t.role}: {t.content}" for t in episode.turns
    )

    prompt = SUMMARIZE_SESSION.format(budget=budget, turns=turns_text)
    result = provider.complete(prompt)

    # Enforce budget on the output
    if counter.count(result) > budget:
        words = result.split()
        max_words = int(budget / 1.3)
        result = " ".join(words[:max_words]) + "..."

    return result
