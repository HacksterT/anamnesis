"""Circle 3 curation queue data model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CurationItem:
    """A candidate fact awaiting human review in the Circle 3 curation queue."""

    id: int
    fact: str
    source_episode: str | None
    source_agent: str | None
    source_url: str | None
    suggested_bolus: str | None
    confidence: float
    status: str  # pending | confirmed | rejected | deferred
    created: str
    reviewed: str | None
