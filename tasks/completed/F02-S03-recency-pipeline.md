---
id: F02-S03
feature: F02
title: Recency Pipeline (Circle 4 → Circle 1)
priority: Must-Have
status: done
created: 2026-04-12
type: software
---

# F02-S03: Recency Pipeline (Circle 4 → Circle 1)

**Feature:** F02 — Circle 4 Episode Capture & Recency Pipeline
**Priority:** Must-Have

## Summary

Wire the fast path from Circle 4 to Circle 1: when a session ends, the most recent context is automatically summarized and injected into the Circle 1 assembly as a system-managed inline bolus. The recency bolus has its own token budget carved out of the overall Circle 1 budget, uses FIFO (new context replaces old), and is invisible to the user's bolus management. This is the core delivery of Phase 2 — the agent remembers what just happened.

## Acceptance Criteria

- [x] When `kf.end_session()` is called, the recency bolus (`_recency`) is automatically created or updated
- [x] The recency bolus contains a summary of the most recent session (via CompletionProvider or heuristic fallback)
- [x] The recency bolus has `render: inline`, a priority in the 21–30 range, and is always active
- [x] The assembler reserves `recency_budget` tokens from the total Circle 1 budget before assembling curated boluses
- [x] Curated boluses get `circle1_max_tokens - recency_budget` tokens; the recency bolus gets up to `recency_budget` tokens
- [x] If `recency_budget` is 0, the recency bolus is not created and the full budget goes to curated boluses
- [x] `kf.get_injection()` includes the recency content inline, positioned after identity boluses but before reference manifest
- [x] The recency bolus is excluded from `kf.list_boluses()` and `kf.delete_bolus()` — it's system-managed, not user-managed
- [x] `kf.get_injection_metrics()` includes a `recency_tokens` field showing how many tokens the recency slot is using
- [x] Warning logged if `recency_budget` exceeds 25% of `circle1_max_tokens`

## Tasks

### Backend

- [x] Add `recency_budget` to `KnowledgeConfig`:
  ```python
  recency_budget: int = 0  # Default: disabled. Set per-agent via config.
  ```
- [x] Create `src/anamnesis/recency/` package with:
  - `pipeline.py` — `update_recency(store, episode, budget, provider=None)` orchestrator
  - `__init__.py` — public exports
- [x] Implement `update_recency()`:
  1. Summarize the episode using `summarize_episode()` from S02, constrained to `recency_budget` tokens
  2. Write or update the `_recency` bolus via the bolus store
  3. Set metadata: `render: inline`, `priority: 25`, `active: True`, `tags: ["_system", "recency"]`
- [x] Modify `KnowledgeFramework.end_session()` to call `update_recency()` after writing the episode
- [x] Modify the assembler to respect recency budget:
  - If `recency_budget > 0`: reserve those tokens, assemble curated boluses with `circle1_max_tokens - recency_budget`
  - The `_recency` bolus is assembled like any other inline bolus but its budget is enforced separately
- [x] Modify `list_boluses()` to exclude system boluses (IDs starting with `_`) by default; add `include_system=False` parameter
- [x] Modify `delete_bolus()` to reject deletion of system boluses
- [x] Update `get_injection_metrics()` to include `recency_tokens` and `recency_budget` fields
- [x] Log warning if `recency_budget > 0.25 * circle1_max_tokens`

### Testing & Verification

- [x] Write test: end_session creates/updates `_recency` bolus with correct metadata
- [x] Write test: assembled injection includes recency content inline at correct priority position
- [x] Write test: curated boluses respect reduced budget (`max_tokens - recency_budget`)
- [x] Write test: recency_budget=0 means no recency bolus, full budget to curated
- [x] Write test: `_recency` bolus excluded from list_boluses() default call
- [x] Write test: `_recency` bolus cannot be deleted via delete_bolus()
- [x] Write test: metrics include recency_tokens field
- [x] Write test: FIFO — second end_session overwrites first recency content
- [x] Write test: warning logged when recency_budget exceeds 25% of max_tokens
- [x] Write test: end-to-end flow — capture turns → end session → get injection → recency content present
- [x] Local Testing: `pytest tests/` passes

### Git

- [ ] Commit, fetch/rebase, push

## Technical Notes

- **System boluses.** The `_recency` bolus introduces the concept of system-managed boluses (IDs starting with `_`). These are invisible to user-facing operations but participate in assembly. Future system boluses might include `_context` (ambient context) or `_agent-profile` (per-agent identity).
- **Budget carve-out, not overflow.** The recency budget is subtracted from the total budget *before* curated assembly. This is a hard reservation, not a soft preference. Curated content cannot spill into the recency slot or vice versa.
- **Priority 25.** The recency bolus sits between identity (1–20) and general knowledge (41–70). This means the agent reads: who you are → what happened recently → what you know. The ordering supports the mental model: orient → contextualize → inform.
- **FIFO is implicit.** There's only one `_recency` bolus. Each `end_session()` overwrites it. No history of past recency content — that history lives in the episodes (Circle 4).
- **The pipeline is synchronous.** `end_session()` → summarize → write bolus → done. No background jobs. If LLM summarization is slow (Gemma 4 on CPU), the heuristic fallback keeps `end_session()` fast.

## Blockers

- F02-S01 (Episode Storage) — depends on episode capture and the `Episode` data model.
- F02-S02 (CompletionProvider) — depends on `summarize_episode()` and the heuristic fallback.
