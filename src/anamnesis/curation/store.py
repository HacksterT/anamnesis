"""SQLite-backed Circle 3 curation queue store."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from anamnesis.curation.model import CurationItem

_SCHEMA = """
CREATE TABLE IF NOT EXISTS curation_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fact TEXT NOT NULL,
    source_episode TEXT,
    source_agent TEXT,
    source_url TEXT,
    suggested_bolus TEXT,
    confidence REAL NOT NULL DEFAULT 0.5,
    status TEXT NOT NULL DEFAULT 'pending',
    created TEXT NOT NULL,
    reviewed TEXT
);

CREATE INDEX IF NOT EXISTS idx_curation_status ON curation_queue(status);
CREATE INDEX IF NOT EXISTS idx_curation_confidence ON curation_queue(confidence DESC);
"""


class CurationStore:
    """SQLite-backed store for the Circle 3 curation queue.

    Shares the same anamnesis.db file as EpisodeStore (WAL mode supports
    concurrent access). The curation_queue table is created on first connect.
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_SCHEMA)

    def stage(
        self,
        fact: str,
        *,
        source_episode: str | None = None,
        source_agent: str | None = None,
        source_url: str | None = None,
        suggested_bolus: str | None = None,
        confidence: float = 0.5,
    ) -> int:
        """Deposit a candidate fact in the queue. Returns the new item id."""
        now = datetime.now(timezone.utc).isoformat()
        with self._conn:
            cursor = self._conn.execute(
                """INSERT INTO curation_queue
                   (fact, source_episode, source_agent, source_url,
                    suggested_bolus, confidence, status, created)
                   VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)""",
                (fact, source_episode, source_agent, source_url,
                 suggested_bolus, confidence, now),
            )
            return cursor.lastrowid

    def list_pending(self, limit: int = 50) -> list[CurationItem]:
        """Return pending items ordered by confidence descending, then created."""
        rows = self._conn.execute(
            """SELECT id, fact, source_episode, source_agent, source_url,
                      suggested_bolus, confidence, status, created, reviewed
               FROM curation_queue
               WHERE status = 'pending'
               ORDER BY confidence DESC, created DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()
        return [_row_to_item(r) for r in rows]

    def get(self, item_id: int) -> CurationItem:
        """Load a single item by id. Raises KeyError if not found."""
        row = self._conn.execute(
            """SELECT id, fact, source_episode, source_agent, source_url,
                      suggested_bolus, confidence, status, created, reviewed
               FROM curation_queue WHERE id = ?""",
            (item_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"Curation item {item_id} not found.")
        return _row_to_item(row)

    def set_status(self, item_id: int, status: str) -> None:
        """Update item status and set reviewed timestamp."""
        now = datetime.now(timezone.utc).isoformat()
        with self._conn:
            cursor = self._conn.execute(
                "UPDATE curation_queue SET status = ?, reviewed = ? WHERE id = ?",
                (status, now, item_id),
            )
        if cursor.rowcount == 0:
            raise KeyError(f"Curation item {item_id} not found.")

    def confirm(self, item_id: int) -> None:
        self.set_status(item_id, "confirmed")

    def reject(self, item_id: int) -> None:
        self.set_status(item_id, "rejected")

    def defer(self, item_id: int) -> None:
        self.set_status(item_id, "deferred")

    def close(self) -> None:
        self._conn.close()


def _row_to_item(row: tuple) -> CurationItem:
    return CurationItem(
        id=row[0],
        fact=row[1],
        source_episode=row[2],
        source_agent=row[3],
        source_url=row[4],
        suggested_bolus=row[5],
        confidence=row[6],
        status=row[7],
        created=row[8],
        reviewed=row[9],
    )
