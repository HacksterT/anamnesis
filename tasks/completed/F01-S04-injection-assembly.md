---
id: F01-S04
feature: F01
title: Injection Assembly (Circle 1)
priority: Must-Have
status: done
created: 2026-04-12
type: software
---

# F01-S04: Injection Assembly (Circle 1)

**Feature:** F01 — Circle 1 & Circle 2 Core
**Priority:** Must-Have

## Summary

Implement the Circle 1 injection assembler — the process that reads active boluses from Circle 2 and assembles the single `anamnesis.md` injection document. The assembler partitions boluses by render mode (`inline` vs `reference`), orders them by priority, renders inline boluses as prose and reference boluses as manifest lines, wraps the result in `<knowledge>` tags, and enforces the token budget. This is the core value delivery of Phase 1: a caller gets a well-formed, token-budgeted knowledge injection document.

## Acceptance Criteria

- [x] `kf.get_injection()` returns a string containing a well-formed `anamnesis.md` document wrapped in `<knowledge>` tags
- [x] Inline boluses (`render: inline`) are rendered as full prose content, ordered by priority
- [x] Reference boluses (`render: reference`) are rendered as manifest lines under `## Available Knowledge`, ordered by priority then alphabetically
- [x] Inline content appears before reference manifest in the assembled document
- [x] Only active boluses are included; inactive boluses are excluded
- [x] `kf.get_injection()` logs a warning when the assembled document exceeds the configured `circle1_max_tokens` (soft max)
- [x] `kf.get_injection()` raises `ValueError` when the assembled document exceeds the hard ceiling (6,000 tokens)
- [x] `kf.assemble()` writes the assembled content to the configured `circle1_path` file and returns the path
- [x] `kf.get_injection_metrics()` returns token count, budget utilization percentage, status, and bolus counts
- [x] Token counting is pluggable via the `TokenCounter` protocol; default `SimpleTokenCounter` uses a word-based heuristic

## Tasks

### Backend

- [x] Implement token counting in `inject/budget.py`:
  - `TokenCounter` protocol: `count(text: str) -> int`
  - `SimpleTokenCounter` — word-based heuristic (`words × 1.3`) as zero-dependency default
  - `BudgetResult` dataclass with `token_count`, `soft_max`, `hard_ceiling`, `status`, and `utilization_pct`
  - `check_budget()` function returning `BudgetResult` with status `ok` / `warning` / `exceeded`

- [x] Implement the assembler in `inject/assembler.py`:
  - `assemble(store, soft_max, hard_ceiling, counter) -> tuple[str, BudgetResult]` — pure function
  - Assembly process:
    1. Query `store.list(active_only=True)` for active boluses
    2. Sort by `priority` (lower first), then alphabetically by `title`
    3. Partition into inline and reference boluses by `render` field
    4. Render inline boluses: read full content via `store.read()`, output as prose
    5. Render reference boluses: format as manifest lines (`- **{title}**: {summary} -> \`{id}\``)
    6. Combine: inline prose first, then `## Available Knowledge` header with manifest lines
    7. Wrap in `<knowledge>` tags
    8. Run token budget check; log warning on soft max, raise `ValueError` on hard ceiling
    9. Return `(assembled_text, budget_result)`

- [x] Wire `KnowledgeFramework` methods:
  - `get_injection() -> str` — calls assembler, returns assembled string
  - `assemble() -> Path` — calls assembler, writes to `circle1_path`, returns path
  - `get_injection_metrics() -> dict` — calls assembler, returns metrics dict with `total_tokens`, `soft_max`, `hard_ceiling`, `utilization_pct`, `status`, `active_boluses`, `total_boluses`

### Testing & Verification

- [x] Write test: empty store produces valid `<knowledge>` document
- [x] Write test: reference boluses appear in manifest with correct format
- [x] Write test: inline boluses rendered as prose, not in manifest
- [x] Write test: inline content appears before reference manifest
- [x] Write test: inactive boluses excluded
- [x] Write test: priority ordering respected
- [x] Write test: assembled document passes `validate_injection()`
- [x] Write test: hard ceiling raises `ValueError`
- [x] Write test: soft max logs warning but succeeds
- [x] Write test: manifest line format matches spec
- [x] Write test: `get_injection()` returns valid document via framework
- [x] Write test: `assemble()` writes file to disk
- [x] Write test: `get_injection_metrics()` returns correct counts
- [x] Write test: end-to-end retrieval flow (get injection → see manifest → retrieve full content)
- [x] Local Testing: `pytest tests/` passes — 75 tests total
- [x] Manual Testing: CHECKPOINT — Notify user to review assembled output

### Git

- [ ] Commit, fetch/rebase, push

## Technical Notes

- **The assembler is a pure function.** `assemble()` takes a store and config values, returns a string and budget result. No side effects. `KnowledgeFramework.assemble()` wraps it with the file-write side effect. `KnowledgeFramework.get_injection()` wraps it without the file write.
- **No section sources in config.** The original design had `identity_source`, `capabilities_source`, `constraints_source`, etc. as config fields. The simplified render model eliminated these — all content comes from boluses. Identity is a bolus with `render: inline, priority: 10`. Constraints are boluses with `render: inline, priority: 90`. No special config needed.
- **Token counting is approximate and that's fine.** The simple heuristic (`words × 1.3`) is within 10-15% of actual token counts for English prose. The budget thresholds are advisory guidelines, not byte-exact limits.
- **The `## Available Knowledge` header** only appears if there are active reference boluses. If all boluses are inline, the manifest section is omitted.
- **The `<knowledge>` wrapper is added by the assembler,** not stored in any source file. Bolus content is raw markdown. The wrapper is an assembly concern.

## Blockers

- F01-S02 (Bolus System) — depends on `BolusStore.list()`, `BolusStore.read()`, and bolus metadata.
- F01-S03 (anamnesis.md Spec) — depends on render model, token budget constants, and validation.
