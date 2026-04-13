"""Episode and Turn data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class Turn:
    """A single conversation turn within an episode."""

    role: Literal["user", "assistant", "system", "tool"]
    content: str
    timestamp: str  # ISO 8601
    sequence: int = 0


@dataclass
class Episode:
    """A conversation session — a sequence of turns."""

    session_id: str
    started: str  # ISO 8601
    ended: str | None = None
    agent: str | None = None
    turns: list[Turn] = field(default_factory=list)
    summary: str | None = None
    turn_count: int = 0
    compiled: bool = False
