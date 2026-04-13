# Anamnesis — Project Roadmap

*Last updated: 2026-04-12*

This document is the single source of truth for where Anamnesis has been, where it is today, and where it is going. It is written for a human reader who wants to understand the project without diving into code or story files.

---

## What Anamnesis Is

Anamnesis is a **knowledge management layer for AI agents**. Its job is to give agents a persistent, curated memory that survives across conversations — and to do so in a way that keeps a human in control of what the agent actually knows.

The core metaphor is medical: a patient's chart. A physician doesn't carry the entire chart in their head for every visit. They have a problem list, a medication list, key history — a curated summary that captures what matters. Everything else is in the record if needed. Anamnesis does the same thing for AI agents.

The design uses a **five-circle model**. Each circle is a different layer of the knowledge system, ordered from most refined (Circle 1, what the agent sees) to least refined (Circle 5, raw behavioral data):

```
Circle 1 — anamnesis.md         The single file injected into the agent's context
Circle 2 — Boluses              The curated knowledge library (one file per topic)
Circle 3 — Curation Queue       Staging area: candidate facts awaiting human review
Circle 4 — Episodes             Raw conversation history (SQLite)
Circle 5 — Behavioral Mining    Pattern extraction from Circle 4 (future)
```

The flow of knowledge moves inward: raw conversations (Circle 4) get compiled into candidate facts (Circle 3), which get confirmed by a human into boluses (Circle 2), which get assembled into the injection file (Circle 1) that the agent reads.

---

## Reading Order

If you want to understand the project from the ground up, read in this order:

1. **`docs/anamnesis/anamnesis-framework.md`** — The theory. Five-circle model, triage questions, the three kinds of knowledge (declarative, episodic, procedural), the reconciliation model. ~1700 lines. Dense but foundational. Read sections 1–4 first, skim the rest.

2. **`docs/anamnesis/anamnesis-construction.md`** — The implementation blueprint. How the framework maps to Python packages, what each module does, key design decisions (library-first, pluggable storage, LLM abstraction). Read this second to understand *why* the code is structured the way it is.

3. **`docs/anamnesis/anamnesis-agent-reference.md`** — The API reference. Every REST endpoint, the retrieve_knowledge tool definition, session lifecycle, CLI commands, Python library surface. This is the document an AI agent (or developer) reads to start using Anamnesis.

4. **This document** — The roadmap. Where everything is and where it's going.

---

## What Has Been Built

### Phase 1 (F01) — Core Library: Circles 1 and 2

*The foundation. Nothing else works without this.*

**What it is:** The bolus system (Circle 2) and injection assembly (Circle 1). A bolus is a single markdown file with YAML frontmatter containing a named piece of knowledge — a persona, a policy, a preference, a skill. The assembler reads all active boluses and builds a single `anamnesis.md` file that gets injected into the agent's system prompt.

**Stories completed:**
- S01: Project scaffolding (uv, pyproject.toml, package structure)
- S02: Bolus system (markdown store, CRUD, validation, slugging)
- S03: `anamnesis.md` specification (XML wrapper, inline vs. reference render modes)
- S04: Injection assembler (token budget enforcement, priority ordering, soft max / hard ceiling)
- S05: REST API (FastAPI wrapper, all bolus endpoints, health check, optional API key auth)
- S06: CLI (`anamnesis init`, `serve`, `assemble`, `validate`, `metrics`, full `bolus` group)
- S07: Web dashboard (SvelteKit, dark theme, five-circle navigation, Circle 1 preview, Circle 2 bolus library)

**Key concepts introduced:**
- **Bolus ID:** lowercase slugs like `cto-knowledge`, `patient-safety`. System boluses start with `_`.
- **Render mode:** `inline` (full content in injection) vs. `reference` (title + summary + pointer in manifest, content loaded on demand)
- **Token budget:** Soft max (4K default, configurable) / hard ceiling (6K). Assembly respects priority order; overflowing the hard ceiling is an error.
- **Active toggle:** Each bolus can be active or inactive. Only active boluses appear in the injection.

---

### Phase 2 (F02) — Circle 4: Episode Capture and Recency

*Short-term memory. The agent can now remember what happened in recent conversations.*

**What it is:** SQLite-backed storage for conversation episodes (Circle 4). An episode is a sequence of turns — user and assistant messages — captured at the end of a session. A recency pipeline compiles the most recent turns into a system bolus (`_recency`) that gets injected alongside the curated knowledge, giving the agent a short-term memory of recent context.

**Stories completed:**
- S01: Episode storage (SQLite schema, `EpisodeStore`, `capture_turn()`, `end_session()`)
- S02: CompletionProvider protocol (`complete(prompt, system) -> str` — the LLM abstraction used by summarization and compilation)
- S03: Recency pipeline (`_recency` bolus, FIFO turn buffer, token budget carve-out)
- S04: Agent API and budget controls (per-agent recency budgets, agent registry in `anamnesis.yaml`)

**Key concepts introduced:**
- **Episode:** A completed conversation session stored in SQLite. Has a session ID, timestamps, agent name, and all turns.
- **CompletionProvider:** A protocol (interface) for making LLM calls. The library never imports Anthropic or OpenAI directly — the application passes in whatever LLM client it uses. Implemented for Ollama in Phase 3.
- **Recency bolus:** A system-managed bolus (`_recency`) that is automatically updated after each `end_session()`. Contains the last N turns up to a configurable token budget. Gives the agent short-term memory without manual work.

---

### Phase 3 (F03) — Multi-Agent Profiles, Curation Queue, Compilation Pipeline

*Long-term learning. The system can now extract knowledge from experience and stage it for human review.*

**What it is:** Three things shipped together. First, per-agent injection profiles so different agents (Ezra, Selah) can share one knowledge base but see different boluses and have isolated recency context. Second, Circle 3 — the curation queue where candidate facts wait for human review before being promoted to boluses. Third, the compilation pipeline that sends uncompiled episodes to an LLM (Gemma 4 locally via Ollama), extracts durable facts as JSON, and deposits them in Circle 3.

**Stories completed:**
- S01: Per-agent bolus activation profiles (agent profiles in `anamnesis.yaml`, additive override model)
- S02: Injection routing and recency isolation (`?agent=ezra` parameter, `_recency-ezra` per-agent boluses)
- S03: Circle 3 schema and curation queue (SQLite `curation_queue` table, `CurationStore`, stage/confirm/reject/defer API)
- S04: Compilation pipeline (`OpenAICompatibleProvider` for Ollama, `compile_episodes()`, tolerant JSON parsing, `POST /v1/compile`, `anamnesis compile`)
- S05: Technical debt (domain exceptions, `Literal` types, assembler single-scan, dashboard CSS consolidation)

**Key concepts introduced:**
- **Agent profile:** A named configuration in `anamnesis.yaml` listing which boluses to activate for that agent. Boluses not in the list fall back to their default active state.
- **Compilation:** The slow-path pipeline from Circle 4 → Circle 3. Triggered explicitly (`kf.compile()` or `anamnesis compile`), never automatically on `end_session()`. Each uncompiled episode is sent to the LLM with an extraction prompt asking for JSON facts. The LLM suggests which bolus each fact belongs to and gives a confidence score (0.0–1.0). Facts are deposited in Circle 3 for human review.
- **Curation queue:** Circle 3. Facts sit here until a human confirms, rejects, or defers them. Confirmed facts are appended to a target bolus (or create a new bolus if the ID doesn't exist). This is the reconciliation step — the human decides what makes it into Circle 2.
- **OpenAICompatibleProvider:** An httpx-based LLM client that works with any OpenAI-compatible endpoint. Configured in `anamnesis.yaml` to point at Ollama running Gemma 4 locally.

---

### Phase 4 (F04) — External Content Intake

*Write pathways. External agents and the dashboard can now push knowledge into the system.*

**What it is:** Two write pathways added. The upsert/append path lets external agents write content directly to named boluses without existence checks (Circle 2 direct write, human-directed). The stage endpoint lets agents deposit candidate facts in Circle 3 for review (agent-autonomous). The Circle 3 dashboard page went from a placeholder to a working curation queue with confirm/reject/defer controls and a manual stage-fact form.

**Stories completed:**
- S01: Bolus upsert and append (`PUT /v1/knowledge/boluses/{id}` creates or replaces, `POST /v1/knowledge/boluses/{id}/append` accumulates with separator)
- S02: External stage endpoint (`POST /v1/curation` with `source_url` field — for agents staging from external sources)
- S03: Dashboard intake UI (Circle 3 page: curation queue with confidence pills, confirm/reject/defer, Stage Fact form; API client additions for curation and upsert/append)

**Key concepts introduced:**
- **Upsert semantics:** `PUT /v1/knowledge/boluses/{id}` returns 201 on create, 200 on update. No 409 conflict errors. The caller doesn't need to check if a bolus exists first.
- **Append:** `POST /v1/knowledge/boluses/{id}/append` adds content to the end of an existing bolus with a configurable separator. Used for accumulating notes, research findings, or facts over time into a single bolus.
- **Routing by provenance:** Human-directed saves go to Circle 2 directly (ground truth, no review needed). Agent-autonomous observations go to Circle 3 (staged, needs confirmation). The distinction is about who decided the content is worth keeping, not about the content itself.

---

## Current State (2026-04-12)

**251 Python tests passing.** Dashboard builds clean.

| Circle | Status | Notes |
|--------|--------|-------|
| Circle 1 | Complete | Injection assembly, token budget, `anamnesis.md` |
| Circle 2 | Complete | Bolus CRUD, upsert/append, markdown store |
| Circle 3 | Complete | Curation queue, confirm/reject/defer, dashboard UI |
| Circle 4 | Complete | Episode capture, recency pipeline, compilation |
| Circle 5 | Not started | Behavioral mining — deferred |

**Dashboard pages:**
| Page | Status |
|------|--------|
| Circle 1 — Injection Preview | Complete |
| Circle 2 — Bolus Library | Complete |
| Circle 3 — Curation Queue | Complete |
| Circle 4 — Episodes | Complete (list view) |
| Circle 5 — Behavioral Mining | Placeholder |
| Settings — Agent Registry | Complete |

---

## What Is Next

### Near Term: Small Gaps

These are backlog items that don't require a new feature canvas — they're extensions of existing work.

| Item | What | Why |
|------|------|-----|
| `anamnesis curation stage` CLI command | Add `stage` subcommand to the `curation` group | Currently you must use the REST API or Python library to stage a fact manually |
| Bolus click-to-edit in dashboard | Inline markdown editor on Circle 2 page | Boluses are currently view-only in the dashboard |
| "Assemble now" button on Circle 1 | Trigger `kf.assemble()` from the dashboard | Currently requires CLI |

---

### Phase 5 — Reconciliation (Circle 3 → Circle 2)

*The payoff for the curation queue. The system learns to promote facts with less manual work.*

**What it would add:**

Right now, confirming a fact requires you to type a target bolus ID in the dashboard. Every fact goes through manual review regardless of confidence. Phase 5 adds:

- **Permissiveness slider:** A per-agent or global configuration (1–5 scale) that controls how much autonomy the system has. Level 1: every fact requires manual confirmation (current behavior). Level 5: facts above a confidence threshold are auto-promoted to their suggested bolus without review.
- **Contradiction detection:** Before confirming a fact, check it against existing boluses for contradictions. If a new fact says "prefer PostgreSQL" and an existing bolus says "prefer MySQL," flag the conflict for manual resolution rather than silently appending.
- **Batch review UI:** The current dashboard confirms one fact at a time. A batch interface would let you review 20 facts in a sitting — scroll, quick-confirm the obvious ones, defer the uncertain ones.

**Why it matters:** Right now you get value from the compilation pipeline only if you sit down and work the curation queue after each compile run. The permissiveness slider lets you set a confidence threshold and walk away — only the uncertain facts land in your queue.

---

### Phase 6 — Dashboard UX Pass

*Bolus editing and quality-of-life improvements.*

**What it would add:**
- Click-to-edit bolus content (markdown editor in the dashboard)
- Sort controls on the bolus list (by name, priority, last updated)
- Bolus detail page (full content view with metadata panel)
- "Assemble now" button on Circle 1

**Why it matters:** The dashboard is the primary human interface for managing knowledge. Right now you can view boluses and toggle them active/inactive, but to edit content you have to use the CLI or edit the markdown files directly. This phase makes the dashboard self-sufficient for routine knowledge maintenance.

---

### Phase 7 — Circle 5: Behavioral Mining

*The system observes patterns in how the agent behaves and extracts procedural knowledge.*

**What it would be:** Circle 5 is about watching what the agent actually does across many episodes and extracting reusable patterns — not just facts ("prefer FastAPI") but procedures ("when starting a new API project, first check for existing FastAPI patterns, then scaffold with uv"). These would be extracted as skill boluses and injected when the matching situation arises.

**Status:** Fully deferred. The framework document (`anamnesis-framework.md`) and the behavioral mining spec (`anamnesis-behavioral-mining.md`) describe the design in detail. Implementation waits until there are enough episodes to make pattern extraction meaningful.

---

### Phase 8 — Vector Search (Only If Needed)

*Full-text and semantic retrieval across the bolus library.*

**What it would be:** FTS5 full-text search over bolus content, and optionally vector similarity search for semantically related boluses. Currently bolus retrieval is categorical — you know the bolus ID and fetch it directly. Vector search would let an agent ask "what do we know about deployment?" and get relevant boluses back without knowing their IDs.

**Status:** Explicitly deferred. The current design (reference render mode + categorical pointers) avoids the need for vector search for most use cases. This phase gets scoped only if there's evidence the categorical model is breaking down — i.e., the bolus library grows large enough that agents can't find what they need with known IDs.

---

## Design Decisions That Won't Change

These are settled and should not be reopened without a strong reason:

- **Library-first.** Anamnesis is a Python library. The REST API is a thin FastAPI wrapper. No tight coupling to any consuming application.
- **Human in the loop.** Nothing goes from Circle 3 to Circle 2 without human confirmation, until Phase 5 introduces the permissiveness slider — and even then, the human sets the threshold.
- **No auto-compilation.** `kf.compile()` is always triggered explicitly. It never runs automatically on `end_session()`. Compilation costs tokens and time; it belongs in a scheduled job or a deliberate manual step.
- **Markdown for boluses.** Circle 2 storage is markdown files with YAML frontmatter. Human-readable, git-friendly, diffable. A SQLite backend is possible in the future but not the default.
- **One database file.** Circles 3 and 4 share `anamnesis.db`. No separate databases per circle.
- **No Docker for development.** `uv run anamnesis serve` and `./start.sh` are sufficient. A deployment Dockerfile can be added later.
- **OpenAI-compatible LLM interface.** The `OpenAICompatibleProvider` works with Ollama, LM Studio, and any OpenAI-compatible endpoint. Gemma 4 Q8 runs locally on the Mac Mini M4 Pro (48GB) via Ollama.

---

## Key Files

| File | What it is |
|------|------------|
| `anamnesis.yaml` | Project configuration: paths, agent profiles, completion provider settings |
| `knowledge/anamnesis.md` | Circle 1 — the assembled injection file the agent reads |
| `knowledge/boluses/` | Circle 2 — one `.md` file per bolus |
| `anamnesis.db` | SQLite database — episodes (Circle 4) and curation queue (Circle 3) |
| `src/anamnesis/framework.py` | The main entry point — `KnowledgeFramework` class, all public methods |
| `src/anamnesis/api/server.py` | FastAPI app factory — all REST endpoints |
| `src/anamnesis/cli.py` | argparse CLI — all `anamnesis` commands |
| `dashboard/src/routes/` | SvelteKit pages — one directory per circle |
| `dashboard/src/lib/api.ts` | TypeScript API client — all dashboard→API calls |
| `docs/anamnesis/` | This directory — framework theory, construction plan, agent reference, roadmap |
| `tasks/completed/` | Finished story files — audit trail of what was built and why |
| `tasks/needed-features.md` | Running status audit of gaps and next steps |
| `tests/` | pytest test suite — 251 tests covering library, API, CLI, pipeline |

---

## How a Session Works End-to-End

This is the lifecycle of knowledge moving through the system, from conversation to confirmed bolus:

```
1. CAPTURE
   Agent calls  POST /v1/episodes/turn  for each message in a conversation.
   At end of session: POST /v1/episodes/end  (with optional agent name + summary).
   → Episode written to SQLite (Circle 4).
   → _recency-{agent} bolus updated with most recent turns (Circle 2).

2. INJECTION (next session)
   Agent calls  GET /v1/knowledge/injection?agent=ezra
   → Assembler reads active boluses (Circle 2) + recency bolus.
   → Returns assembled anamnesis.md as plain text.
   Agent puts this in its system prompt.

3. COMPILATION (scheduled or manual)
   Run  anamnesis compile  (or POST /v1/compile).
   → Each uncompiled episode is sent to the LLM (Gemma 4 via Ollama).
   → LLM returns JSON: [{fact, suggested_bolus, confidence}, ...]
   → Facts deposited in curation queue (Circle 3).
   → Episode marked compiled.

4. CURATION (human review)
   Open dashboard → Circle 3.
   For each pending fact:
     - Confirm → type target bolus ID → fact appended to that bolus (or new bolus created).
     - Reject → fact discarded (stays in DB for audit).
     - Defer → stays in queue for later.

5. PROMOTION (on confirm)
   Confirmed fact is appended to the target bolus file (Circle 2).
   Next time the agent starts a session, the fact is in its injection.
```

---

## Ports

| Port | Service |
|------|---------|
| 8741 | Anamnesis REST API |
| 5175 | Dashboard dev server (SvelteKit) |
| 4173 | Dashboard preview |

Start both with `./start.sh` from the repo root.

---

*For the full theory, read `anamnesis-framework.md`. For the API surface, read `anamnesis-agent-reference.md`. For implementation details, read the source — it's clean and commented.*
