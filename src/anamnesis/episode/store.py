"""SQLite-backed episode storage for Circle 4."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from anamnesis.episode.model import Episode, Turn

_SCHEMA = """
CREATE TABLE IF NOT EXISTS episodes (
    session_id TEXT PRIMARY KEY,
    agent TEXT,
    started TEXT NOT NULL,
    ended TEXT,
    summary TEXT,
    turn_count INTEGER NOT NULL DEFAULT 0,
    compiled BOOLEAN NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS turns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES episodes(session_id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    sequence INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_turns_session ON turns(session_id);
CREATE INDEX IF NOT EXISTS idx_episodes_ended ON episodes(ended);
CREATE INDEX IF NOT EXISTS idx_episodes_compiled ON episodes(compiled);
CREATE INDEX IF NOT EXISTS idx_episodes_agent ON episodes(agent);
"""


class EpisodeStore:
    """SQLite-backed storage for conversation episodes."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.executescript(_SCHEMA)

    def save(self, episode: Episode) -> None:
        """Write an episode and its turns to the database."""
        with self._conn:
            self._conn.execute(
                """INSERT OR REPLACE INTO episodes
                   (session_id, agent, started, ended, summary, turn_count, compiled)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    episode.session_id,
                    episode.agent,
                    episode.started,
                    episode.ended,
                    episode.summary,
                    episode.turn_count,
                    episode.compiled,
                ),
            )
            # Delete existing turns (for replace case) then insert
            self._conn.execute(
                "DELETE FROM turns WHERE session_id = ?", (episode.session_id,)
            )
            self._conn.executemany(
                """INSERT INTO turns (session_id, role, content, timestamp, sequence)
                   VALUES (?, ?, ?, ?, ?)""",
                [
                    (episode.session_id, t.role, t.content, t.timestamp, t.sequence)
                    for t in episode.turns
                ],
            )

    def load(self, session_id: str) -> Episode:
        """Load a full episode with turns. Raises KeyError if not found."""
        row = self._conn.execute(
            "SELECT * FROM episodes WHERE session_id = ?", (session_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"Episode '{session_id}' not found.")

        turn_rows = self._conn.execute(
            "SELECT role, content, timestamp, sequence FROM turns "
            "WHERE session_id = ? ORDER BY sequence",
            (session_id,),
        ).fetchall()

        turns = [Turn(role=r[0], content=r[1], timestamp=r[2], sequence=r[3]) for r in turn_rows]

        return Episode(
            session_id=row[0],
            agent=row[1],
            started=row[2],
            ended=row[3],
            summary=row[4],
            turn_count=row[5],
            compiled=bool(row[6]),
            turns=turns,
        )

    def list(self, agent: str | None = None, limit: int = 50) -> list[dict]:
        """List episode metadata (no turns). Optionally filter by agent."""
        if agent:
            rows = self._conn.execute(
                "SELECT session_id, agent, started, ended, summary, turn_count, compiled "
                "FROM episodes WHERE agent = ? ORDER BY started DESC LIMIT ?",
                (agent, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT session_id, agent, started, ended, summary, turn_count, compiled "
                "FROM episodes ORDER BY started DESC LIMIT ?",
                (limit,),
            ).fetchall()

        return [
            {
                "session_id": r[0],
                "agent": r[1],
                "started": r[2],
                "ended": r[3],
                "has_summary": r[4] is not None,
                "turn_count": r[5],
                "compiled": bool(r[6]),
            }
            for r in rows
        ]

    def get_latest(self, agent: str | None = None) -> Episode | None:
        """Return the most recent episode, or None if no episodes exist."""
        if agent:
            row = self._conn.execute(
                "SELECT session_id FROM episodes WHERE agent = ? ORDER BY started DESC LIMIT 1",
                (agent,),
            ).fetchone()
        else:
            row = self._conn.execute(
                "SELECT session_id FROM episodes ORDER BY started DESC LIMIT 1"
            ).fetchone()

        if row is None:
            return None
        return self.load(row[0])

    def cleanup(self, retention_days: int) -> int:
        """Delete episodes older than retention_days. Returns count deleted."""
        cutoff = (
            datetime.now(timezone.utc) - timedelta(days=retention_days)
        ).isoformat()
        with self._conn:
            cursor = self._conn.execute(
                "DELETE FROM episodes WHERE ended IS NOT NULL AND ended < ?",
                (cutoff,),
            )
            return cursor.rowcount

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()
