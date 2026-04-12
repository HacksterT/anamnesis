---
id: F02-S01
feature: F02
title: Episode Storage & Capture API
priority: Must-Have
status: done
created: 2026-04-12
type: software
---

# F02-S01: Episode Storage & Capture API

**Feature:** F02 — Circle 4 Episode Capture & Recency Pipeline
**Priority:** Must-Have

## Summary

Implement the Circle 4 episode storage system — the raw conversation capture layer. An episode is a single session's conversation turns stored in a SQLite database. This story delivers the data model, the capture API (`capture_turn`, `end_session`), SQLite storage with configurable retention, and REST endpoints for episode management. After this story, any agent can log its conversations into Anamnesis.

SQLite is chosen over JSON files because Circles 3, 4, and 5 all need indexed queries (retention by date, compilation status, behavioral pattern lookups). One `anamnesis.db` file with separate tables per circle avoids building a JSON file scanner now and migrating later. Python's `sqlite3` is stdlib — no new dependencies.

## Acceptance Criteria

- [x] `kf.capture_turn(role, content)` appends a turn to the current in-memory session
- [x] `kf.end_session()` writes the session to the `episodes` table in `{circle4_root}/anamnesis.db`
- [x] `kf.end_session(summary="...")` accepts an optional human-provided summary
- [x] Session IDs are UTC timestamp-based by default (`2026-04-12T14-30-00Z`), with optional custom IDs
- [x] Episode schema includes: `session_id`, `agent` (nullable), `started`, `ended`, `turn_count`, `summary`, `compiled` (boolean, for Phase 3)
- [x] Turns are stored in a separate `turns` table with foreign key to episode: `turn_id`, `session_id`, `role`, `content`, `timestamp`, `sequence`
- [x] `kf.list_episodes()` returns metadata for stored episodes (ID, agent, start time, turn count, has summary) — no turn content
- [x] `kf.get_episode(session_id)` returns the full episode with all turns
- [x] Episode retention: `kf.cleanup_episodes()` runs `DELETE FROM episodes WHERE ended < ?` using `circle4_retention_days`; called automatically on `end_session()`
- [x] `circle4_root` and `circle4_retention_days` are added to `KnowledgeConfig`
- [x] REST endpoints: `POST /v1/episodes/turn`, `POST /v1/episodes/end`, `GET /v1/episodes`, `GET /v1/episodes/{id}`
- [x] Database is created automatically on first use (no manual migration step)

## Tasks

### Backend

- [x] Add Circle 4 fields to `KnowledgeConfig`:
  ```python
  circle4_root: Path | None = None          # Directory for anamnesis.db. None = disabled.
  circle4_retention_days: int | None = None  # Days to retain episodes. None = indefinite.
  ```
- [x] Create `src/anamnesis/episode/` package with:
  - `model.py` — `Turn` and `Episode` dataclasses
  - `store.py` — `EpisodeStore` class (SQLite-backed)
  - `__init__.py` — public exports
- [x] Implement `Turn` dataclass:
  ```python
  @dataclass
  class Turn:
      role: str          # "user" | "assistant" | "system" | "tool"
      content: str
      timestamp: str     # ISO 8601
      sequence: int      # Order within the session
  ```
- [x] Implement `Episode` dataclass:
  ```python
  @dataclass
  class Episode:
      session_id: str
      agent: str | None       # Which agent captured this. None = unspecified.
      started: str            # ISO 8601
      ended: str | None
      turns: list[Turn]
      summary: str | None
      turn_count: int
      compiled: bool = False  # Has this episode been processed by Phase 3 compilation?
  ```
- [x] Implement `EpisodeStore` (SQLite-backed):
  - `__init__(db_path)` — opens/creates the SQLite database, runs schema migration
  - Schema:
    ```sql
    CREATE TABLE IF NOT EXISTS episodes (
        session_id TEXT PRIMARY KEY,
        agent TEXT,
        started TEXT NOT NULL,
        ended TEXT,
        summary TEXT,
        turn_count INTEGER NOT NULL DEFAULT 0,
        compiled BOOLEAN NOT NULL DEFAULT FALSE
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
    ```
  - `save(episode)` — insert episode row + turn rows in a transaction
  - `load(session_id)` — join episode + turns, return `Episode`
  - `list(agent=None, limit=50)` — return metadata (no turns), optionally filtered by agent
  - `cleanup(retention_days)` — `DELETE FROM episodes WHERE ended < ?` (cascade deletes turns)
  - `get_latest(agent=None)` — return the most recent episode (for recency pipeline)
- [x] Wire `KnowledgeFramework` methods:
  - `capture_turn(role, content)` — appends to in-memory session (creates session on first call)
  - `end_session(summary=None, agent=None)` — writes episode to SQLite, resets in-memory state, runs cleanup if retention configured
  - `list_episodes(agent=None)` — delegates to store
  - `get_episode(session_id)` — delegates to store
- [x] Add REST endpoints to the API:
  ```
  POST /v1/episodes/turn         -> capture a turn (JSON body: role, content)
  POST /v1/episodes/end          -> end session (optional JSON body: summary, agent)
  GET  /v1/episodes              -> list episodes (metadata only, ?agent= filter)
  GET  /v1/episodes/{session_id} -> full episode content with turns
  ```
- [x] Update config loader to handle new `circle4_root` and `circle4_retention_days` fields
- [x] Database auto-creation: `EpisodeStore.__init__` creates the db and tables if they don't exist

### Testing & Verification

- [x] Write test: capture multiple turns, end session, verify episode and turns in SQLite
- [x] Write test: session ID is generated from UTC timestamp by default
- [x] Write test: custom session ID is accepted and used
- [x] Write test: list_episodes returns metadata without turn content
- [x] Write test: list_episodes filters by agent name
- [x] Write test: get_episode returns full content including turns in sequence order
- [x] Write test: retention cleanup deletes old episodes and their turns (cascade)
- [x] Write test: capture_turn without end_session does not write to SQLite (in-memory only)
- [x] Write test: get_latest returns the most recent episode
- [x] Write test: compiled flag defaults to False
- [x] Write test: REST endpoints for turn capture, session end, episode listing
- [x] Write test: database is created automatically on first use
- [x] Local Testing: `pytest tests/` passes

### Git

- [ ] Commit, fetch/rebase, push

## Technical Notes

- **SQLite, not JSON files.** Circles 3, 4, and 5 all need indexed queries. One `anamnesis.db` file in `circle4_root` serves all three. The `episodes` and `turns` tables are Circle 4. Future phases add `curation_queue` (Circle 3) and `observations` / `patterns` (Circle 5) tables to the same database. This avoids per-circle storage migration.
- **In-memory session state.** The `KnowledgeFramework` holds one active session at a time. `capture_turn` appends to it. `end_session` writes it to SQLite and resets. If the process crashes before `end_session`, the in-memory turns are lost. This is acceptable for Phase 2 — durable mid-session persistence (WAL-based append) is a future concern.
- **Retention runs on write.** `cleanup_episodes()` is called during `end_session()`, not on a schedule. The SQLite `DELETE` with an index on `ended` is fast regardless of table size.
- **Circle 4 is optional.** If `circle4_root` is None, episode capture is disabled. `capture_turn` and `end_session` are no-ops. The SQLite database is never created.
- **The `compiled` column.** Not used in Phase 2. It exists so Phase 3 (compilation pipeline) can query `WHERE compiled = FALSE` to find unprocessed episodes without a schema migration.
- **The `agent` column.** Allows per-agent episode filtering. When Atlas and Selah both capture episodes into the same database, `list_episodes(agent="atlas")` returns only Atlas's sessions.
- **CASCADE delete.** Deleting an episode row automatically deletes its turns. This keeps retention cleanup to a single DELETE statement.
- **No ORM.** Raw `sqlite3` module with parameterized queries. The schema is simple enough that an ORM adds overhead without value.

## Blockers

- F01 (Phase 1) — depends on `KnowledgeConfig`, `KnowledgeFramework`, and the API layer. All complete.
