"""Recency pipeline — updates the system-managed _recency bolus."""

from __future__ import annotations

import logging

from anamnesis.bolus.base import BolusStore
from anamnesis.completion.provider import CompletionProvider
from anamnesis.completion.summarizer import summarize_episode
from anamnesis.episode.model import Episode

logger = logging.getLogger(__name__)

RECENCY_BOLUS_ID = "_recency"
RECENCY_PRIORITY = 25
RECENCY_TAGS = ["_system", "recency"]


def recency_bolus_id(agent: str | None = None) -> str:
    """Return the recency bolus ID for a given agent."""
    if agent:
        return f"_recency-{agent}"
    return RECENCY_BOLUS_ID


def update_recency(
    store: BolusStore,
    episode: Episode,
    budget: int,
    provider: CompletionProvider | None = None,
    agent: str | None = None,
) -> None:
    """Summarize an episode and write/update the recency bolus.

    If agent is specified, writes to _recency-{agent} instead of _recency.
    Each agent gets its own recency bolus — ending an Atlas session
    doesn't affect Selah's recency.

    If budget is 0, the recency bolus is deleted if it exists.
    """
    bolus_id = recency_bolus_id(agent)

    if budget <= 0:
        store.delete(bolus_id)
        return

    summary = summarize_episode(episode, budget, provider=provider)

    if not summary.strip():
        return

    metadata = {
        "id": bolus_id,
        "title": f"Recent Context ({agent})" if agent else "Recent Context",
        "active": True,
        "render": "inline",
        "priority": RECENCY_PRIORITY,
        "summary": f"System-managed recency for {agent}." if agent else "System-managed recency context.",
        "tags": RECENCY_TAGS,
    }

    store.write(bolus_id, summary, metadata)
