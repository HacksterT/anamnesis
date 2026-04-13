---
id: F04-S03
feature: F04
title: Dashboard Intake UI
priority: Should-Have
status: done
created: 2026-04-12
type: software
---

# F04-S03: Dashboard Intake UI

**Feature:** F04 — External Content Intake
**Priority:** Should-Have

## Summary

Replace the Circle 3 placeholder page with a fully functional curation queue UI. Add API client support for upsert and append. The curation queue is the primary human interface for reviewing facts extracted by the compilation pipeline or staged by external agents — without this, `/curate` stages facts but there's no ergonomic way to confirm them into boluses.

## Acceptance Criteria

- [x] Circle 3 page shows all pending curation items (fact, confidence, source agent, suggested bolus)
- [x] Each item has Confirm / Reject / Defer actions
- [x] Confirm prompts for a target bolus ID before promoting
- [x] Rejected and deferred items disappear from the pending view after action
- [x] A "Stage Fact" form on Circle 3 lets the user manually add a fact to the queue
- [x] API client includes: `getCurationQueue`, `stageFact`, `confirmItem`, `rejectItem`, `deferItem`
- [x] API client includes: `upsertBolus`, `appendBolus`
- [x] Dashboard builds without errors

## Tasks

### API Client

- [x] Add `CurationItem` interface to `api.ts`
- [x] Add `getCurationQueue()` → `GET /v1/curation`
- [x] Add `stageFact(data)` → `POST /v1/curation`
- [x] Add `confirmItem(id, bolusId)` → `POST /v1/curation/{id}/confirm`
- [x] Add `rejectItem(id)` → `POST /v1/curation/{id}/reject`
- [x] Add `deferItem(id)` → `POST /v1/curation/{id}/defer`
- [x] Add `upsertBolus(id, data)` → `PUT /v1/knowledge/boluses/{id}`
- [x] Add `appendBolus(id, content, separator?)` → `POST /v1/knowledge/boluses/{id}/append`

### Circle 3 Page

- [x] Replace placeholder with working curation queue component
- [x] Pending items list: fact text, confidence pill w/ color, source metadata (agent, URL), suggested bolus tag
- [x] Confirm flow: inline input for target bolus ID → POST confirm
- [x] Reject: single click, item disappears, list re-fetches
- [x] Defer: single click, item re-fetches
- [x] "Stage Fact" form: fact textarea, optional suggested bolus, confidence slider (0–1)
- [x] Empty state when queue is empty with CLI hint
- [x] Error banner on API failures

### Testing & Verification

- [x] Dashboard builds: `npm run build` — clean build, no errors

### Git

- [ ] Commit pending

## Technical Notes

- Confirm requires a bolus ID. The user may type an existing bolus ID or a new one (upsert semantics on the backend: if new, creates it). Validate format client-side: lowercase alphanumeric + hyphens.
- Confidence bar: treat the `confidence` float (0.0–1.0) as a visual indicator, not editable in this phase.
- The Circle 3 page has no dependency on Circle 4 being configured — facts can be staged directly via the API even without an episode database.

## Blockers

- F03-S03 (Circle 3 Schema) — Complete ✓
- F04-S02 (External Stage Endpoint) — Complete ✓
