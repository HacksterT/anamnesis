---
id: F03-S03
feature: F03
title: Circle 3 Schema & Curation Queue
priority: Must-Have
status: done
created: 2026-04-12
type: software
---

# F03-S03: Circle 3 Schema & Curation Queue

**Feature:** F03 — Agent Profiles, Injection Routing & Compilation Pipeline
**Priority:** Must-Have

## Summary

Design and implement the Circle 3 curation queue — the staging area where extracted facts wait for human review before becoming permanent boluses in Circle 2. This story builds the data model, the SQLite schema, the CRUD operations (stage, confirm, reject, defer), and the REST + CLI interfaces. It does NOT implement the compilation pipeline that populates the queue — that's S04.

## Acceptance Criteria

- [x] `curation_queue` table exists in `anamnesis.db` (same database as episodes)
- [x] `kf.stage(fact, source_episode, suggested_bolus, confidence, agent)` adds a fact to the queue
- [x] `kf.get_curation_queue(limit=20)` returns pending items ordered by confidence descending
- [x] `kf.confirm(item_id, bolus_id)` promotes the fact: appends content to the target bolus (or creates a new one) and removes from queue
- [x] `kf.reject(item_id)` marks the item as rejected and removes from active queue
- [x] `kf.defer(item_id)` keeps the item in the queue but deprioritizes it
- [x] REST endpoints: `GET /v1/curation`, `POST /v1/curation/{id}/confirm`, `POST /v1/curation/{id}/reject`, `POST /v1/curation/{id}/defer`
- [x] CLI: `anamnesis curation list`, `anamnesis curation confirm <id> --bolus <bolus_id>`, `anamnesis curation reject <id>`, `anamnesis curation defer <id>`
- [ ] Dashboard Circle 3 page shows the curation queue with confirm/reject/defer controls — deferred to later sprint

## Tasks

### Backend

- [x] Design and create `curation_queue` SQLite table with `source_url` field added (F04-S02 requirement incorporated)
- [x] Create `src/anamnesis/curation/` package with `model.py`, `store.py`, `__init__.py`
- [x] Implement `CurationStore` methods: `stage()`, `list_pending()`, `set_status()`, `confirm()`, `reject()`, `defer()`, `get(id)`
- [x] Wire `KnowledgeFramework` methods: `stage()`, `get_curation_queue()`, `confirm()`, `reject()`, `defer()`
- [x] `confirm()` logic: appends to existing bolus or creates new one, then marks confirmed
- [x] Add REST endpoints to API server
- [x] Add CLI `curation` command group

### Frontend (Dashboard)

- [ ] Rewrite Circle 3 page from placeholder to functional curation queue — deferred to later sprint

### Testing & Verification

- [x] Write test: stage a fact, retrieve from queue
- [x] Write test: confirm promotes fact to Circle 2 bolus
- [x] Write test: reject marks item, excluded from pending list
- [x] Write test: defer keeps item but deprioritizes
- [x] Write test: queue ordered by confidence descending
- [x] Write test: REST endpoints for curation CRUD
- [x] Write test: stage fails cleanly without circle4_root
- [x] Local Testing: `pytest tests/` passes — 231 tests passing (212 pre-existing + 19 new)

### Git

- [ ] Commit, fetch/rebase, push

## Technical Notes

- **Same database.** The `curation_queue` table goes in `anamnesis.db` alongside `episodes` and `turns`. The `EpisodeStore` already opens this database; the `CurationStore` shares the connection or opens the same file.
- **Confirm appends, doesn't replace.** When a fact is confirmed into an existing bolus, the content is appended (with a separator), not replaced. This preserves existing curated content. If the bolus doesn't exist, a new one is created.
- **Confidence scores come from the compilation pipeline (S04).** For manually staged facts (via `kf.stage()` directly), confidence defaults to 0.5.
- **Rejected items are soft-deleted.** They stay in the table with `status: rejected` for audit purposes but don't appear in the pending queue.

## Blockers

- F02-S01 (Episode Storage) — shares the SQLite database.
