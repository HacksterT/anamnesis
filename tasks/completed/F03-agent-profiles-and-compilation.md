---
id: F03
title: Agent Profiles, Injection Routing & Compilation Pipeline
status: done
created: 2026-04-12
---

# F03: Agent Profiles, Injection Routing & Compilation Pipeline

## Overview

**Feature:** Phase 3 — Per-agent injection profiles and the Circle 4 → Circle 3 compilation pipeline.
**Problem:** Two gaps block the multi-agent personal use case and the next layer of knowledge intelligence. First, Atlas and Selah currently see identical injections — there's no way to give Atlas coding boluses while Selah gets theology boluses from the same library. Second, episodes accumulate in Circle 4 but nothing extracts durable knowledge from them. The recency pipeline gives short-term memory; the compilation pipeline gives long-term learning.
**Goal:** Agents get tailored injections from a shared knowledge base via activation profiles and isolated recency. The compilation pipeline extracts candidate facts from episodes and deposits them in Circle 3 for human curation.

## Context

The personal instance runs one Anamnesis API serving two agents: Atlas (TypeScript, Claude-based) and Selah (Python, local Gemma 4). Both share the same bolus library and episode database. Phase 2 built the episode capture and recency pipeline, but with single-agent assumptions — one `_recency` bolus, one injection for all agents, no per-agent bolus filtering.

Phase 3 has two halves:
1. **Agent profiles (S01–S02):** Per-agent bolus activation, injection routing, and recency isolation. This is the prerequisite for the Atlas + Selah shared deployment.
2. **Compilation pipeline (S03–S04):** LLM-powered extraction of durable facts from episodes into Circle 3. This is the first use of `CompletionProvider` for real analytical work (beyond summarization).

## Premortem

1. **Per-agent activation complexity.** If every bolus has a per-agent active/inactive override, the data model gets complex fast. Keep it simple: an agent profile is a list of bolus IDs to activate. Boluses not in the list use their default `active` state.

2. **Compilation quality depends on the model.** Claude will produce excellent extractions. Gemma 4 may produce mediocre ones. The pipeline needs a confidence signal and must never auto-promote to Circle 2 — everything goes through Circle 3 curation.

3. **Circle 3 schema design lock-in.** The curation queue schema will be hard to change once episodes are being compiled into it. Get the schema right in S03 — review with the user before implementing.

4. **Compilation cost.** Each episode sent to an LLM for extraction costs tokens/money. The pipeline should be triggered explicitly (`kf.compile()`) or on configurable thresholds, never on every `end_session()`.

5. **Agent profile UI complexity.** Showing a matrix of agents × boluses in the dashboard could be overwhelming. Start with a simple list view per agent, not a full matrix.

## Stories

| ID | Title | Priority | Status |
|----|-------|----------|--------|
| F03-S01 | Per-Agent Bolus Activation Profiles | Must-Have | Done |
| F03-S02 | Injection Routing & Recency Isolation | Must-Have | Done |
| F03-S03 | Circle 3 Schema & Curation Queue | Must-Have | Done |
| F03-S04 | Compilation Pipeline (Circle 4 → Circle 3) | Must-Have | Done |
| F03-S05 | Technical Debt Cleanup | Should-Have | Done |

## Non-Goals

- **Auto-promotion from Circle 3 to Circle 2.** All compiled facts require human confirmation in this phase. The permissiveness slider (allowing auto-promotion at high confidence) is Phase 4.
- **Dashboard bolus editing.** A markdown editor for inline bolus editing is a UX improvement, not a Phase 3 concern.
- **Multi-tenant support.** Per-agent profiles solve the personal multi-agent case. Multi-tenant (multiple users with isolated knowledge) is handled by the consuming application (Selah's gateway), not Anamnesis.
- **Vector search.** Still deferred. Compilation uses LLM extraction, not embedding similarity.
- **Behavioral mining (Circle 5).** Phase 6 per build order.

## Dependencies

- **F01 + F02 complete.** Bolus system, assembler, API, CLI, dashboard, episode storage, recency pipeline, CompletionProvider, agent registry.
- **A CompletionProvider implementation.** For compilation in S04. The heuristic fallback doesn't work here — extraction requires an LLM. The user provides Claude or Gemma 4 via the protocol.

## Success Metrics

- `GET /v1/knowledge/injection?agent=atlas` returns Atlas-specific injection with only Atlas's activated boluses and Atlas's recency context
- `GET /v1/knowledge/injection?agent=selah` returns a different injection with Selah's boluses and Selah's recency
- `kf.compile()` processes uncompiled episodes and deposits extracted facts in the Circle 3 curation queue
- `kf.get_curation_queue()` returns pending facts for human review
- `kf.confirm(item_id, bolus="target-bolus")` promotes a fact to Circle 2
- `kf.reject(item_id)` removes a fact from the queue
- The dashboard Settings page shows per-agent bolus activation toggles
- The dashboard Circle 3 page shows the curation queue with confirm/reject/defer controls

## Design Decisions (Resolved)

- **Agent profiles are additive overrides.** An agent profile contains a list of bolus IDs to activate FOR that agent. Boluses not in the list fall back to their default `active` state. This means you can have a bolus that's active by default (everyone sees it) and one that's only activated for specific agents.
- **Recency is per-agent.** System boluses become `_recency-{agent_name}`. Each agent's `end_session(agent="atlas")` writes to its own recency bolus. The assembler includes only the matching agent's recency bolus when `?agent=` is specified.
- **Circle 3 uses the same SQLite database.** A `curation_queue` table in `anamnesis.db` alongside `episodes` and `turns`. No new database files.
- **Compilation is explicit.** `kf.compile()` is called by the application (CLI command, cron job, post-session hook). Not triggered automatically by `end_session()`.

## Open Design Decisions

- **Extraction prompt template.** The prompt for extracting facts from episodes is critical to quality. Should be configurable per application. Default template TBD in S04 implementation.
- **Curation queue priority.** How are items in the queue ordered? By confidence score? By recency? By source agent? Leaning toward confidence descending, with recency as tiebreaker.

---

*Created: 2026-04-12*
