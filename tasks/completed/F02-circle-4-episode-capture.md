---
id: F02
title: Circle 4 — Episode Capture & Recency Pipeline
status: completed
created: 2026-04-12
---

# F02: Circle 4 — Episode Capture & Recency Pipeline

## Overview

**Feature:** Anamnesis Phase 2 — Circle 4 (Episode Capture) + Recency Pipeline to Circle 1
**Problem:** Anamnesis manages curated, durable knowledge — but agents also need recent conversation context. Custom agents like Atlas and Selah have no built-in conversation history management. Without a recency mechanism, every conversation starts cold. The agent knows who you are and what you know, but not what you were doing five minutes ago.
**Goal:** A conversation capture system (Circle 4) that stores raw episodes and a recency pipeline that automatically surfaces the most recent context into Circle 1 as a token-budgeted inline bolus. The pipeline is capped, FIFO, and configurable per agent — the disciplined alternative to context stuffing.

## Context

Phase 1 established the core loop: boluses in Circle 2, assembly into Circle 1, retrieval via `retrieve_knowledge`. But Circle 1 currently contains only curated, static knowledge. It has no awareness of what happened in the last conversation.

The two pilot agents illustrate the need:
- **Atlas** (Claude-based personal assistant) — currently relies on Claude Code's internal conversation management. When Anamnesis replaces Atlas's memory system, it needs to handle recency itself.
- **Selah** (local Gemma 4 theological knowledge base) — has no conversation management at all. Every session is a blank slate.

The recency pipeline solves this with a two-path architecture:
1. **Fast path (this phase):** Circle 4 → Circle 1 recency slot. Automatic, capped, FIFO. Recent context lands in the injection as a system-managed inline bolus.
2. **Slow path (Phase 3):** Circle 4 → Circle 3 → Circle 2 compilation. Extracts durable facts from episodes through curation. Not in this phase.

This phase also introduces the `CompletionProvider` protocol — the abstraction that lets Anamnesis call any LLM for summarization without importing specific model SDKs. This was deferred from Phase 1 and is needed now for auto-summarization of episodes into the recency slot.

## Premortem

What could go wrong:

1. **CompletionProvider scope creep.** The protocol is meant to be a thin abstraction (`complete(prompt) -> str`). If we try to handle streaming, tool use, multi-turn, or model-specific features, it becomes an SDK wrapper. Keep it to one method.

2. **Recency eats the curated budget.** If a user sets recency_budget to 800 on a 2,000 token injection, curated knowledge gets starved. The system should warn when recency exceeds 25% of the total budget, but not prevent it — the user decides.

3. **Episode storage grows unbounded.** Conversation turns accumulate fast. Without retention from day one, the episode directory becomes a storage problem. Retention with configurable TTL is mandatory, not a nice-to-have.

4. **Summarization quality on local models.** Gemma 4 may produce poor summaries compared to Claude. The heuristic fallback (last N turns truncated to budget) must be a real, tested code path — not just a theoretical backup.

5. **Testing without a real LLM.** The CompletionProvider needs a mock implementation that's useful for testing, not just a stub that returns empty strings. A `StaticCompletionProvider` that returns canned responses is the minimum.

## Stories

| ID | Title | Priority | Status |
|----|-------|----------|--------|
| F02-S01 | Episode Storage & Capture API | Must-Have | Done |
| F02-S02 | CompletionProvider Protocol | Must-Have | Done |
| F02-S03 | Recency Pipeline (Circle 4 → Circle 1) | Must-Have | Done |
| F02-S04 | Agent API & Budget Controls | Must-Have | Done |

## Non-Goals

- **Compilation Pipeline (Circle 4 → Circle 3).** Extracting durable facts from episodes is Phase 3. This phase captures episodes and pipes recency to Circle 1 — it does not analyze episode content for knowledge extraction.
- **Circle 3 (Curation Layer).** No reconciliation queue, no staging area. Still deferred.
- **Episode Viewer UI.** The dashboard does not get an episode browsing view in this phase. Episodes are accessible via API and CLI.
- **Multi-Agent Episode Isolation.** All episodes go to the same Circle 4 directory. Per-agent episode isolation is a future concern if the shared model proves insufficient.
- **Streaming or Real-Time Capture.** Episodes are captured turn-by-turn via explicit API calls, not by intercepting live conversations. The agent's runtime calls `capture_turn()` — Anamnesis doesn't hook into the transport layer.
- **Memory Migration.** Translating Atlas's existing memories into boluses is a separate concern, not part of Circle 4 capture.

## Dependencies

- **F01 (Phase 1)** — bolus system, assembler, API, CLI, agent registry. All complete.
- **A CompletionProvider implementation** — for auto-summarization. Phase 2 ships a heuristic fallback; real LLM summarization requires the application to provide a CompletionProvider (Claude, Gemma, etc.).
- **SQLite (stdlib).** Episode storage uses Python's built-in `sqlite3`. One `anamnesis.db` file in `circle4_root` with tables for episodes and turns. Same database will serve Circle 3 (curation queue) and Circle 5 (behavioral observations) in future phases. No external database dependency.

## Success Metrics

- `kf.capture_turn(role, content)` appends a turn to the current episode; `kf.end_session()` closes it
- Episodes are stored as files in a configurable Circle 4 directory, with retention enforcement
- The assembled `anamnesis.md` includes a recency section with content from the most recent session
- Recency token budget is configurable per agent (0–1000 tokens) via CLI, API, and dashboard slider
- Setting `recency_budget: 0` disables the recency pipeline entirely
- The recency slot respects its token budget — content is truncated or summarized to fit
- The system works without a CompletionProvider (heuristic fallback) and with one (LLM summarization)
- Episode retention automatically cleans up episodes older than `circle4_retention_days`

## Design Decisions (Resolved)

- **Episode storage format.** SQLite, not JSON files. Episodes are high-volume machine-generated data that needs indexed queries (retention by date, compilation status, per-agent filtering). One `anamnesis.db` file in `circle4_root` with `episodes` and `turns` tables. Same database will host Circle 3 and Circle 5 tables in future phases. Python's `sqlite3` is stdlib — no new dependencies.
- **Session identity.** Sessions are identified by a UTC timestamp-based ID (`2026-04-12T14-30-00Z`). The caller can also provide a custom session ID. Session IDs must be filesystem-safe.
- **Recency bolus is system-managed.** It has a reserved bolus ID (`_recency`), `render: inline`, and a priority in the 21–30 range (after identity, before general knowledge). The user doesn't create, edit, or delete it directly — the pipeline manages it.
- **CompletionProvider is optional.** The library ships a heuristic summarizer (`last N turns, truncated to budget`) as the default. Applications that want LLM-quality summaries provide a `CompletionProvider`. This keeps the library zero-LLM-dependency.
- **Recency budget is separate from the main token budget.** The assembler reserves `recency_budget` tokens from the total Circle 1 budget before assembling curated boluses. This means curated content gets `circle1_max_tokens - recency_budget` tokens. The recency slot cannot overflow into curated space.

## Open Design Decisions

- **Turn metadata richness.** Turns store role, content, timestamp, and sequence order. Richer metadata (token count, tool calls, model used) deferred to Phase 3 when the compilation pipeline may need it. Adding columns to SQLite is cheap.
- **Auto-summarization prompt.** The prompt template for LLM summarization is TBD. It should be configurable per application but have a sensible default. Defer the exact prompt to S02/S03 implementation.

---

*Created: 2026-04-12*
