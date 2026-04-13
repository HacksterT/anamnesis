---
id: F03-S02
feature: F03
title: Injection Routing & Recency Isolation
priority: Must-Have
status: done
created: 2026-04-12
type: software
---

# F03-S02: Injection Routing & Recency Isolation

**Feature:** F03 — Agent Profiles, Injection Routing & Compilation Pipeline
**Priority:** Must-Have

## Summary

Route injection assembly through agent profiles so each agent gets a tailored `anamnesis.md`. Isolate recency boluses per agent so Atlas and Selah don't overwrite each other's recent context. After this story, `GET /v1/knowledge/injection?agent=atlas` returns Atlas's injection, and `?agent=selah` returns Selah's.

## Acceptance Criteria

- [ ] `GET /v1/knowledge/injection?agent=atlas` assembles using Atlas's activation profile + Atlas's recency bolus
- [ ] `GET /v1/knowledge/injection?agent=selah` returns a different injection using Selah's profile + Selah's recency
- [ ] `GET /v1/knowledge/injection` (no agent param) returns the default injection (all default-active boluses, shared recency)
- [ ] `kf.get_injection(agent="atlas")` works at the library level
- [ ] `kf.end_session(agent="atlas")` writes to `_recency-atlas` instead of `_recency`
- [ ] `kf.end_session(agent="selah")` writes to `_recency-selah`
- [ ] Each agent's recency bolus is independent — ending an Atlas session doesn't affect Selah's recency
- [ ] `GET /v1/knowledge/injection/metrics?agent=atlas` returns agent-specific metrics
- [ ] The assembler applies the agent's activation profile: default-active boluses + agent-specific activations, excluding the other agent's recency boluses

## Tasks

### Backend

- [ ] Add `agent` parameter to `KnowledgeFramework.get_injection(agent=None)`
- [ ] Add `agent` parameter to `KnowledgeFramework.get_injection_metrics(agent=None)`
- [ ] Modify assembler to accept an optional agent activation profile (list of bolus IDs to include)
- [ ] Modify recency pipeline: `update_recency()` writes to `_recency-{agent}` when agent is specified, `_recency` when not
- [ ] Modify assembler: when `agent` is specified, include only `_recency-{agent}`, exclude other `_recency-*` boluses
- [ ] Modify `list_boluses(include_system=True)` to return all recency boluses for visibility
- [ ] Update API injection endpoints to accept `?agent=` query parameter
- [ ] Update API metrics endpoint to accept `?agent=` query parameter
- [ ] Update CLI `assemble` and `metrics` to accept `--agent` flag

### Testing & Verification

- [ ] Write test: two agents get different injections from the same bolus library
- [ ] Write test: agent-specific recency boluses don't interfere
- [ ] Write test: default (no agent) injection still works
- [ ] Write test: agent activation profile correctly filters boluses
- [ ] Write test: metrics reflect agent-specific token usage
- [ ] Write test: API routing with `?agent=` parameter
- [ ] Local Testing: `pytest tests/` passes

### Git

- [ ] Commit, fetch/rebase, push

## Technical Notes

- **Recency bolus naming:** `_recency-{agent}` follows the system bolus convention (underscore prefix). The assembler includes only the matching agent's recency bolus. System boluses not matching the agent pattern are excluded.
- **Activation profile resolution:** For a given agent, the active bolus set is: (boluses where `active: true` by default) UNION (boluses in the agent's `active_boluses` list). An agent cannot deactivate a default-active bolus in this model — that would require an `excluded_boluses` list, which adds complexity. Defer exclusion to a future iteration if needed.
- **Backward compatibility:** All endpoints continue to work without `?agent=`. The default behavior is unchanged — no agent means no profile filtering, shared recency.

## Blockers

- F03-S01 (Agent Profiles) — depends on the `active_boluses` field in agent config.
