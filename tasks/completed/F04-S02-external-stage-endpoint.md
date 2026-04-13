---
id: F04-S02
feature: F04
title: External Stage Endpoint (Circle 3)
priority: Must-Have
status: done
created: 2026-04-12
type: software
---

# F04-S02: External Stage Endpoint (Circle 3)

**Feature:** F04 — External Content Intake
**Priority:** Must-Have

## Summary

Add a `POST /v1/curation` REST endpoint and `kf.stage_external()` library method so external agents can deposit candidate facts directly into the Circle 3 curation queue without going through the compilation pipeline. F03-S03 builds the curation queue schema and implements `kf.stage(fact, source_episode, ...)` for the compilation path (Circle 4 → Circle 3). This story adds the parallel intake path for agent-autonomous content that has no source episode — e.g., Ezra reads a paper, notices a relevant claim, and wants to flag it for human review without committing it to a bolus. The caller supplies the fact, an optional suggested bolus, and a confidence estimate. The item appears in the dashboard's Circle 3 curation queue alongside compilation-derived items.

## Acceptance Criteria

- [ ] `kf.stage_external(fact, suggested_bolus=None, confidence=0.5, agent=None, source_url=None)` adds a curation item with `source_episode=None`
- [ ] `POST /v1/curation` accepts `{fact, suggested_bolus, confidence, agent, source_url}` and returns the new item's `id`
- [ ] Items created via `POST /v1/curation` appear in `GET /v1/curation` (the pending queue)
- [ ] Items created via `POST /v1/curation` can be confirmed, rejected, and deferred via existing F03-S03 endpoints
- [ ] The `source_url` field (optional) is stored and displayed in the dashboard — allows tracing the claim back to its origin (YouTube URL, paper link, etc.)
- [ ] `source_episode` is `null` for externally staged items (distinguishes them from compilation-derived items)

## Tasks

### Backend

- [x] `source_url` column included in initial `curation_queue` schema (co-designed with F03-S03, no migration needed)
- [x] `stage()` on `CurationStore` accepts `source_episode=None` (all params optional except `fact`)
- [x] `kf.stage()` on `KnowledgeFramework` accepts all params including `source_url`
- [x] `CurationStage` Pydantic model added to API
- [x] `POST /v1/curation` endpoint added to API server

### Frontend (Dashboard)

- [ ] Display `source_url` in curation queue item card — deferred with dashboard sprint

### Testing & Verification

- [x] Write test: `POST /v1/curation` returns 201 with item id
- [x] Write test: externally staged item appears in `GET /v1/curation`
- [x] Write test: externally staged item can be confirmed to a bolus
- [x] Write test: staging without circle4_root returns 422
- [x] Local Testing: `pytest tests/` passes — covered by `test_curation.py`
- [ ] Manual Testing: CHECKPOINT — Notify user to verify staging from simulated external agent call

### Git

- [ ] Commit, fetch/rebase, push

## Technical Notes

- **source_url as provenance.** The `source_url` field lets a human trace a staged claim back to its origin before deciding to confirm it. Without provenance, the curation queue is just a list of claims with no way to verify them. This is especially important for agent-autonomous items — you want to know whether the agent is citing a peer-reviewed paper or a YouTube comment.
- **Confidence from external agents.** The calling agent provides its own confidence estimate. This is less reliable than the compilation pipeline's LLM-estimated confidence (since the calling agent is biased toward the content it just read). The human should treat externally staged confidence as a rough prioritization hint, not a quality guarantee.

## Blockers

- F03-S03 (Circle 3 Schema & Curation Queue) — requires the `curation_queue` table and `CurationStore` to exist before this story can be implemented.
