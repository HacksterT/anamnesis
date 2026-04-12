"""Heuristic summarizer — no LLM needed."""

from __future__ import annotations

from anamnesis.episode.model import Episode
from anamnesis.inject.budget import SimpleTokenCounter, TokenCounter


class HeuristicSummarizer:
    """Summarizes episodes without any LLM call.

    Strategy: take the last N turns that fit within the token budget,
    formatted as a compact prose block.
    """

    def __init__(self, counter: TokenCounter | None = None) -> None:
        self._counter = counter or SimpleTokenCounter()

    def summarize(self, episode: Episode, budget: int) -> str:
        """Produce a summary of the episode within the token budget."""
        if not episode.turns:
            return ""

        # If there's a human-provided summary, use it (truncated if needed)
        if episode.summary:
            return self._truncate(episode.summary, budget)

        # Build a date prefix
        date_str = episode.started[:10] if episode.started else "Unknown date"
        prefix = f"Last session ({date_str}): "
        prefix_tokens = self._counter.count(prefix)
        remaining = budget - prefix_tokens

        if remaining <= 0:
            return self._truncate(prefix.rstrip(": "), budget)

        # Take turns from the end, fitting within budget
        parts: list[str] = []
        tokens_used = 0

        for turn in reversed(episode.turns):
            line = f"{turn.role}: {turn.content}"
            line_tokens = self._counter.count(line)
            if tokens_used + line_tokens > remaining:
                break
            parts.append(line)
            tokens_used += line_tokens

        if not parts:
            # Can't fit even one turn — truncate the last turn
            last = episode.turns[-1]
            line = f"{last.role}: {last.content}"
            return self._truncate(prefix + line, budget)

        parts.reverse()
        result = prefix + " ".join(parts)

        # Final budget enforcement
        if self._counter.count(result) > budget:
            result = self._truncate(result, budget)

        return result

    def _truncate(self, text: str, budget: int) -> str:
        """Truncate text to fit within token budget."""
        words = text.split()
        # budget / 1.3 ≈ max words
        max_words = int(budget / 1.3)
        if len(words) <= max_words:
            return text
        return " ".join(words[:max_words]) + "..."
