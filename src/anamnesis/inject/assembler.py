"""Injection assembler — builds anamnesis.md from active boluses."""

from __future__ import annotations

import logging

from anamnesis.bolus.base import BolusStore
from anamnesis.inject.budget import BudgetResult, SimpleTokenCounter, TokenCounter, check_budget
from anamnesis.inject.schema import RENDER_INLINE, RENDER_REFERENCE, TOKEN_HARD_CEILING

logger = logging.getLogger(__name__)


def assemble(
    store: BolusStore,
    soft_max: int = 4000,
    hard_ceiling: int = TOKEN_HARD_CEILING,
    counter: TokenCounter | None = None,
) -> tuple[str, BudgetResult]:
    """Assemble an anamnesis.md document from active boluses.

    Pure function. Reads active boluses from the store, renders them
    by render mode (inline first, then reference manifest), wraps in
    <knowledge> tags, and checks token budget.

    Returns (assembled_text, budget_result).
    Raises ValueError if hard ceiling is exceeded.
    """
    if counter is None:
        counter = SimpleTokenCounter()

    boluses = store.list(active_only=True)

    # Sort by priority (lower first), then alphabetically by title
    boluses.sort(key=lambda b: (b.get("priority", 50), b.get("title", "")))

    # Partition by render mode
    inline_boluses = [b for b in boluses if b.get("render") == RENDER_INLINE]
    reference_boluses = [b for b in boluses if b.get("render") == RENDER_REFERENCE]

    parts: list[str] = []

    # Render inline boluses as prose (full content)
    for meta in inline_boluses:
        content = store.read(meta["id"])
        if content.strip():
            parts.append(content.strip())

    # Render reference boluses as manifest
    if reference_boluses:
        manifest_lines: list[str] = []
        for meta in reference_boluses:
            title = meta.get("title", meta["id"])
            summary = meta.get("summary", "")
            bolus_id = meta["id"]
            manifest_lines.append(f"- **{title}**: {summary} -> `{bolus_id}`")

        parts.append("## Available Knowledge\n" + "\n".join(manifest_lines))

    # Assemble
    inner = "\n\n".join(parts)
    text = f"<knowledge>\n{inner}\n</knowledge>"

    # Budget check
    budget = check_budget(text, counter, soft_max, hard_ceiling)

    if budget.status == "exceeded":
        raise ValueError(
            f"Injection exceeds hard ceiling: {budget.token_count} tokens "
            f"(ceiling: {hard_ceiling}). Demote inline boluses to reference "
            f"or deactivate boluses to reduce size."
        )

    if budget.status == "warning":
        logger.warning(
            "Injection exceeds soft max: %d tokens (soft max: %d, utilization: %.1f%%)",
            budget.token_count,
            soft_max,
            budget.utilization_pct,
        )

    return text, budget
