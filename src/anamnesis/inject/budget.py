"""Token counting and budget enforcement."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from anamnesis.inject.schema import TOKEN_HARD_CEILING, TOKEN_SOFT_MAX_DEFAULT

# Words-to-tokens ratio for English prose heuristic
WORDS_TO_TOKENS_RATIO = 1.3


@runtime_checkable
class TokenCounter(Protocol):
    """Protocol for pluggable token counting."""

    def count(self, text: str) -> int: ...


class SimpleTokenCounter:
    """Word-based heuristic token counter (zero dependencies).

    Approximates token count as words * WORDS_TO_TOKENS_RATIO. Within
    10-15% of actual counts for English prose.
    """

    def count(self, text: str) -> int:
        return int(len(text.split()) * WORDS_TO_TOKENS_RATIO)


@dataclass
class BudgetResult:
    """Result of a token budget check."""

    token_count: int
    soft_max: int
    hard_ceiling: int
    status: str  # "ok" | "warning" | "exceeded"

    @property
    def utilization_pct(self) -> float:
        if self.soft_max == 0:
            return 0.0
        return round((self.token_count / self.soft_max) * 100, 1)


def check_budget(
    text: str,
    counter: TokenCounter,
    soft_max: int = TOKEN_SOFT_MAX_DEFAULT,
    hard_ceiling: int = TOKEN_HARD_CEILING,
) -> BudgetResult:
    """Check token budget for assembled injection text."""
    token_count = counter.count(text)

    if token_count > hard_ceiling:
        status = "exceeded"
    elif token_count > soft_max:
        status = "warning"
    else:
        status = "ok"

    return BudgetResult(
        token_count=token_count,
        soft_max=soft_max,
        hard_ceiling=hard_ceiling,
        status=status,
    )
