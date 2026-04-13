---
id: F03-S05
feature: F03
title: Technical Debt Cleanup
priority: Should-Have
status: done
created: 2026-04-12
type: software
---

# F03-S05: Technical Debt Cleanup

**Feature:** F03 — Agent Profiles, Injection Routing & Compilation Pipeline
**Priority:** Should-Have

## Summary

Address the technical debt items identified during the simplify pass. These are housekeeping improvements that reduce fragility and improve developer experience before the codebase grows with Circles 3–5 implementation.

## Acceptance Criteria

- [x] Custom exception types: `BolusExistsError`, `BolusNotFoundError`, `CircleNotConfiguredError` replace generic exceptions
- [x] API error handling uses exception types instead of string matching
- [x] `typing.Literal` used for `BudgetResult.status`, `KnowledgeConfig.bolus_store`, `Turn.role`
- [x] `BolusUpdate.summary` removed (field was dead — `update_bolus()` takes only content)
- [x] Dashboard CSS cleanup: `.page-header`, `.error-banner`, `.muted`, `.create-form`, `.form-row`, `.btn-primary`, `.btn-danger-sm` removed from circle-1 and settings pages, consolidated in `app.css`
- [x] `get_injection_metrics()` avoids redundant bolus reads — assembler now populates `budget.total_boluses` and `budget.active_boluses` from its single `store.list()` call

## Tasks

### Backend

- [x] Create `src/anamnesis/exceptions.py` with domain exception types
- [x] Update `framework.py` to raise domain exceptions
- [x] Update `api/server.py` to catch domain exceptions instead of string matching
- [x] Add `Literal` type annotations to relevant fields
- [x] Remove `BolusUpdate.summary` dead field
- [x] Refactor `get_injection_metrics()` — assembler now returns bolus counts via `BudgetResult`

### Frontend

- [x] Extract remaining duplicated CSS from Circle 1 and Settings pages to `app.css`

### Testing & Verification

- [x] Update tests — adjusted one match string for `CircleNotConfiguredError` message
- [x] Local Testing: 251 tests passing

### Git

- [ ] Commit pending

## Blockers

- None — can be done in parallel with other F03 stories.
