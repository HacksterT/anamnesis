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


def update_recency(
    store: BolusStore,
    episode: Episode,
    budget: int,
    provider: CompletionProvider | None = None,
) -> None:
    """Summarize an episode and write/update the _recency bolus.

    The recency bolus is a system-managed inline bolus that contains
    a summary of the most recent session. It's overwritten on each call
    (FIFO — new context replaces old).

    If budget is 0, the recency bolus is deleted if it exists.
    """
    if budget <= 0:
        store.delete(RECENCY_BOLUS_ID)  # returns False if not found
        return

    summary = summarize_episode(episode, budget, provider=provider)

    if not summary.strip():
        return

    metadata = {
        "id": RECENCY_BOLUS_ID,
        "title": "Recent Context",
        "active": True,
        "render": "inline",
        "priority": RECENCY_PRIORITY,
        "summary": "System-managed recency context from last session.",
        "tags": RECENCY_TAGS,
    }

    store.write(RECENCY_BOLUS_ID, summary, metadata)
