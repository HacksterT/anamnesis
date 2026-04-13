---
id: F03-S03
feature: F03
title: Circle 3 Schema & Curation Queue
priority: Must-Have
status: backlog
created: 2026-04-12
type: software
---

# F03-S03: Circle 3 Schema & Curation Queue

**Feature:** F03 — Agent Profiles, Injection Routing & Compilation Pipeline
**Priority:** Must-Have

## Summary

Design and implement the Circle 3 curation queue — the staging area where extracted facts wait for human review before becoming permanent boluses in Circle 2. This story builds the data model, the SQLite schema, the CRUD operations (stage, confirm, reject, defer), and the REST + CLI interfaces. It does NOT implement the compilation pipeline that populates the queue — that's S04.

## Acceptance Criteria

- [ ] `curation_queue` table exists in `anamnesis.db` (same database as episodes)
- [ ] `kf.stage(fact, source_episode, suggested_bolus, confidence, agent)` adds a fact to the queue
- [ ] `kf.get_curation_queue(limit=20)` returns pending items ordered by confidence descending
- [ ] `kf.confirm(item_id, bolus_id)` promotes the fact: appends content to the target bolus (or creates a new one) and removes from queue
- [ ] `kf.reject(item_id)` marks the item as rejected and removes from active queue
- [ ] `kf.defer(item_id)` keeps the item in the queue but deprioritizes it
- [ ] REST endpoints: `GET /v1/curation`, `POST /v1/curation/{id}/confirm`, `POST /v1/curation/{id}/reject`, `POST /v1/curation/{id}/defer`
- [ ] CLI: `anamnesis curation list`, `anamnesis curation confirm <id> --bolus <bolus_id>`, `anamnesis curation reject <id>`
- [ ] Dashboard Circle 3 page shows the curation queue with confirm/reject/defer controls

## Tasks

### Backend

- [ ] Design and create `curation_queue` SQLite table:
  ```sql
  CREATE TABLE IF NOT EXISTS curation_queue (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      fact TEXT NOT NULL,
      source_episode TEXT,
      source_agent TEXT,
      suggested_bolus TEXT,
      confidence REAL DEFAULT 0.5,
      status TEXT NOT NULL DEFAULT 'pending',  -- pending, confirmed, rejected, deferred
      created TEXT NOT NULL,
      reviewed TEXT
  );
  CREATE INDEX IF NOT EXISTS idx_curation_status ON curation_queue(status);
  CREATE INDEX IF NOT EXISTS idx_curation_confidence ON curation_queue(confidence);
  ```
- [ ] Create `src/anamnesis/curation/` package with:
  - `model.py` — `CurationItem` dataclass
  - `store.py` — `CurationStore` class (SQLite-backed, uses existing `anamnesis.db`)
  - `__init__.py` — public exports
- [ ] Implement `CurationStore` methods: `stage()`, `list_pending()`, `confirm()`, `reject()`, `defer()`, `get(id)`
- [ ] Wire `KnowledgeFramework` methods: `stage()`, `get_curation_queue()`, `confirm()`, `reject()`, `defer()`
- [ ] `confirm()` logic: read the fact content, either append to an existing bolus or create a new one, then mark the queue item as confirmed
- [ ] Add REST endpoints to API server
- [ ] Add CLI `curation` command group

### Frontend (Dashboard)

- [ ] Rewrite Circle 3 page from placeholder to functional curation queue
- [ ] Show pending items with fact content, source episode, suggested bolus, confidence score
- [ ] Confirm button: prompts for target bolus (or accepts suggestion), calls API
- [ ] Reject button: calls API, removes from visible list
- [ ] Defer button: calls API, moves to bottom of list

### Testing & Verification

- [ ] Write test: stage a fact, retrieve from queue
- [ ] Write test: confirm promotes fact to Circle 2 bolus
- [ ] Write test: reject marks item, excluded from pending list
- [ ] Write test: defer keeps item but deprioritizes
- [ ] Write test: queue ordered by confidence descending
- [ ] Write test: REST endpoints for curation CRUD
- [ ] Local Testing: `pytest tests/` passes

### Git

- [ ] Commit, fetch/rebase, push

## Technical Notes

- **Same database.** The `curation_queue` table goes in `anamnesis.db` alongside `episodes` and `turns`. The `EpisodeStore` already opens this database; the `CurationStore` shares the connection or opens the same file.
- **Confirm appends, doesn't replace.** When a fact is confirmed into an existing bolus, the content is appended (with a separator), not replaced. This preserves existing curated content. If the bolus doesn't exist, a new one is created.
- **Confidence scores come from the compilation pipeline (S04).** For manually staged facts (via `kf.stage()` directly), confidence defaults to 0.5.
- **Rejected items are soft-deleted.** They stay in the table with `status: rejected` for audit purposes but don't appear in the pending queue.

## Blockers

- F02-S01 (Episode Storage) — shares the SQLite database.
