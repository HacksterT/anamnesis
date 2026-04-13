---
id: F04
title: External Content Intake
status: done
created: 2026-04-12
---

# F04: External Content Intake

## Overview

**Feature:** External Content Intake — Circle 2 direct write and Circle 3 staging from external agents.
**Problem:** External agents (Ezra, research pipelines) can synthesize knowledge from external sources — YouTube transcripts, papers, curated guides — but have no ergonomic pathway to get that content into the bolus system. The existing `POST /v1/knowledge/boluses` is a strict create-only operation that 409s if the bolus already exists. There's no upsert, no append-to-existing-bolus, and no way for an external agent to stage a candidate fact into Circle 3 without first building a full episode and running the compilation pipeline.
**Goal:** An external agent can call a single API endpoint to either write content directly to a named Circle 2 bolus (human-directed, ground truth) or stage it in Circle 3 for review (agent-autonomous, needs confirmation). The "AI Memory Research" bolus can be created on first call and appended to on every subsequent call — without the calling agent managing existence state.

## Context

The Karpathy LLM Wiki pattern (see `docs/karpathy-llm-wiki.md`) describes a three-layer architecture: raw sources, a persistent wiki, and a schema. The "Ingest" operation is the core workflow — an agent reads a source, synthesizes it, and integrates the result into the wiki. The wiki is the persistent, compounding artifact; the agent does the bookkeeping.

Anamnesis maps onto this pattern directly:
- **Raw sources** → Circle 4 (episodes) or external files the agent reads
- **The wiki** → Circle 2 boluses
- **The schema** → `anamnesis.yaml` + Circle 1 injection spec

F04 implements the missing "Ingest" operation — the write pathway from external synthesis back into the bolus system. Without this, the LLM Wiki pattern works for reading (injection is well-implemented) but breaks at the write step.

The critical routing decision comes from provenance, not content type:
- **Human-directed save** ("I want to retain this") → Circle 2 directly. The user's judgment is ground truth. No reconciliation queue needed.
- **Agent-autonomous detection** ("this might be worth keeping") → Circle 3 staging. Requires human confirmation before Circle 2.

F04-S01 implements the Circle 2 direct write path. F04-S02 adds the Circle 3 staging endpoint for agent-autonomous writes (once F03-S03 builds the curation queue schema). F04-S03 adds a dashboard UI for human-initiated paste/upload intake.

## Stories

| ID | Title | Priority | Status |
|----|-------|----------|--------|
| F04-S01 | Bolus Upsert & Append | Must-Have | Done |
| F04-S02 | External Stage Endpoint (Circle 3) | Must-Have | Done |
| F04-S03 | Dashboard Intake UI | Should-Have | Done |

## Non-Goals

- **Auto-promotion from Circle 3 to Circle 2.** Confirmed facts require human action. That's F03/F04's reconciliation work.
- **Source document storage.** Anamnesis does not store raw YouTube transcripts or source PDFs. The agent does that synthesis externally and pushes only the curated result.
- **Full-text search across boluses.** F04 is about write pathways, not retrieval. FTS5 is a future feature.
- **Conflict resolution.** Upsert replaces content on existing boluses. Merge strategies are deferred.

## Dependencies

- **F01 + F02 + F03-S01 + F03-S02 complete.** Bolus CRUD, injection assembly, agent profiles. ✓
- **F03-S03 (Circle 3 Schema)** — required before F04-S02 can be implemented.

## Success Metrics

- [x] `PUT /v1/knowledge/boluses/{id}` creates the bolus if it doesn't exist, updates content if it does — no 409, no existence check required by the caller
- [x] `POST /v1/knowledge/boluses/{id}/append` appends content to an existing bolus with a configurable separator
- [x] `kf.upsert_bolus("ai-memory-research", content)` works in library code
- [x] `kf.append_bolus("ai-memory-research", new_content)` works in library code
- [x] `POST /v1/curation` (F04-S02) creates a Circle 3 staging item without requiring a source episode
- [x] External agent (Ezra) can ingest a synthesized guide into a named bolus in a single API call
- [x] Claude Code `/compact` skill stages session knowledge to Circle 3 for human review

## Design Decisions (Resolved)

- **Append separator is configurable per-call.** Default `\n\n---\n\n` (horizontal rule in markdown). Callers pass `separator` in the request body to override.
- **Upsert accepts optional metadata.** `PUT /v1/knowledge/boluses/{id}` body accepts `title`, `summary`, `tags`, `render`, `priority` — used only when creating; silently ignored on update.
- **PUT semantics changed from strict-update to upsert.** Previously returned 404 when bolus didn't exist. Now returns 201. One test updated to reflect this intentional change.

## Open Design Decisions

- **F04-S02 scope boundary with F03-S03.** The `kf.stage()` method and `curation_queue` table are built in F03-S03. F04-S02 only adds the `POST /v1/curation` REST endpoint and `source_url` field. Confirm this split when F03-S03 is scheduled.

---

*Created: 2026-04-12 | S01 completed: 2026-04-12 | S02 completed: 2026-04-12 | S03 completed: 2026-04-12*
