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
    agent: str | None = None,
    agent_active_boluses: list[str] | None = None,
) -> tuple[str, BudgetResult]:
    """Assemble an anamnesis.md document from active boluses.

    Args:
        agent: If specified, only include the matching recency bolus
            (_recency-{agent}) and exclude other agents' recency boluses.
        agent_active_boluses: Additional bolus IDs to activate for this
            agent beyond the defaults. Boluses in this list are included
            even if their default active state is False.

    Returns (assembled_text, budget_result).
    Raises ValueError if hard ceiling is exceeded.
    """
    if counter is None:
        counter = SimpleTokenCounter()

    # Get all boluses (active and inactive) if we have agent overrides
    if agent_active_boluses:
        all_boluses = store.list(active_only=False)
        boluses = []
        for b in all_boluses:
            bid = b.get("id", "")
            if b.get("active", True) or bid in agent_active_boluses:
                boluses.append(b)
    else:
        boluses = store.list(active_only=True)

    # Filter recency boluses by agent
    if agent:
        my_recency = f"_recency-{agent}"
        boluses = [
            b for b in boluses
            if not b.get("id", "").startswith("_recency")
            or b.get("id") == my_recency
        ]
    else:
        # No agent specified — include _recency (shared) but exclude agent-specific ones
        boluses = [
            b for b in boluses
            if not (b.get("id", "").startswith("_recency-"))
        ]

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
