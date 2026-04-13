---
id: F03-S05
feature: F03
title: Technical Debt Cleanup
priority: Should-Have
status: backlog
created: 2026-04-12
type: software
---

# F03-S05: Technical Debt Cleanup

**Feature:** F03 — Agent Profiles, Injection Routing & Compilation Pipeline
**Priority:** Should-Have

## Summary

Address the technical debt items identified during the simplify pass. These are housekeeping improvements that reduce fragility and improve developer experience before the codebase grows with Circles 3–5 implementation.

## Acceptance Criteria

- [ ] Custom exception types: `BolusExistsError`, `BolusNotFoundError`, `CircleNotConfiguredError` replace generic exceptions
- [ ] API error handling uses exception types instead of string matching
- [ ] `typing.Literal` used for `BudgetResult.status`, `KnowledgeConfig.bolus_store`, `Turn.role`
- [ ] `BolusUpdate` model either wires `summary` through to framework or removes the field
- [ ] Dashboard CSS cleanup: remaining duplicated styles extracted to `app.css`
- [ ] `get_injection_metrics()` avoids redundant bolus reads (assembler returns metadata it loaded)

## Tasks

### Backend

- [ ] Create `src/anamnesis/exceptions.py` with domain exception types
- [ ] Update `framework.py` to raise domain exceptions
- [ ] Update `api/server.py` to catch domain exceptions instead of string matching
- [ ] Add `Literal` type annotations to relevant fields
- [ ] Fix `BolusUpdate.summary` — either wire through or remove
- [ ] Refactor `get_injection_metrics()` to avoid double-scan (have assembler return bolus metadata)

### Frontend

- [ ] Extract remaining duplicated CSS from Circle 1 and Settings pages to `app.css`

### Testing & Verification

- [ ] Update tests to check for new exception types
- [ ] Local Testing: `pytest tests/` passes, dashboard builds
- [ ] Verify type checker (`ruff check` or `mypy`) is happy with Literal types

### Git

- [ ] Commit, fetch/rebase, push

## Blockers

- None — can be done in parallel with other F03 stories.
