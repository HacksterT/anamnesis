"""Shared test helpers."""

from datetime import datetime, timedelta, timezone

from anamnesis.episode.model import Episode, Turn


def make_episode(
    session_id: str = "test-session",
    agent: str | None = None,
    n_turns: int = 3,
    summary: str | None = None,
) -> Episode:
    """Create a test episode with the given number of turns."""
    now = datetime.now(timezone.utc)
    turns = [
        Turn(
            role="user" if i % 2 == 0 else "assistant",
            content=f"Turn {i} content",
            timestamp=(now + timedelta(seconds=i * 10)).isoformat(),
            sequence=i,
        )
        for i in range(n_turns)
    ]
    return Episode(
        session_id=session_id,
        agent=agent,
        started=now.isoformat(),
        ended=(now + timedelta(minutes=5)).isoformat(),
        turns=turns,
        summary=summary,
        turn_count=n_turns,
    )
