# Anamnesis

A knowledge management framework for LLM agent systems. Library-first Python package that manages curated knowledge injection into any LLM via a single markdown file (`anamnesis.md`).

## Project State

- **Phase 1 (F01) complete.** S01–S07: scaffolding, bolus system, injection spec, assembler, API, CLI, dashboard. 
- **Phase 2 (F02) complete.** S01–S04: SQLite episode storage, CompletionProvider protocol, recency pipeline, agent API + budget controls.
- **184 tests passing.** Python test suite covers library, API, CLI, episodes, completion, recency.
- **Knowledge directory:** `knowledge/anamnesis.md` (Circle 1) and `knowledge/boluses/` (Circle 2). Episodes in SQLite (`anamnesis.db`).
- **Dashboard:** SvelteKit app in `/dashboard` with bolus library, injection preview, agent registry with recency slider.

## Key Architecture Documents

- `docs/anamnesis/anamnesis-framework.md` — The full framework (five-circle model, triage questions, declarative/procedural/episodic knowledge, transport layer inversion, reconciliation model). ~1700 lines. This is the theory.
- `docs/anamnesis/anamnesis-construction.md` — The construction plan (Python library, package structure, API surface, build order). This is the implementation blueprint.
- `tasks/completed/F01-circle-1-and-2-core.md` — Phase 1 PRD feature canvas. Circle 1 + Circle 2.
- `tasks/completed/F01-S01` through `F01-S07` — Phase 1 implementation stories (all complete).
- `tasks/F02-circle-4-episode-capture.md` — Phase 2 PRD feature canvas. Circle 4 + recency pipeline.
- `tasks/F02-S01` through `F02-S04` — Phase 2 implementation stories (all complete).
- `tasks/needed-features.md` — Future features, migration tooling, and technical debt.

## Design Decisions (Settled)

- **Injection format:** Markdown with `<knowledge>` XML outer wrapper. Not JSON, not TOML, not YAML. Markdown wins on token density and LLM training distribution for knowledge injection.
- **Injection file name:** `anamnesis.md` (not CLAUDE.md). LLM-agnostic.
- **Circle 2 storage:** Markdown files with YAML frontmatter. Curation-friendly, git-friendly. Pluggable `BolusStore` interface for future SQLite backend.
- **Bolus activation model:** Not all boluses appear in every injection. Each bolus has an `active` toggle. Phase 1: static toggles. Future: dynamic manifest assembly based on context.
- **Token counting:** Pluggable `TokenCounter` protocol. Default: word-based heuristic (zero dependencies). Users plug in model-specific tokenizers.
- **Token budget bounds:** 500 min / 1K-2.5K target / 4K soft max (configurable) / 6K hard ceiling.
- **Architecture:** Library-first. Python library is the core product. FastAPI REST API is a thin wrapper for LLM-agnostic HTTP access.
- **Package manager:** uv (not pip).
- **No Docker for development.** Convenience Dockerfile in S05 for deployment.
- **API auth:** Optional API key via config. Unauthenticated by default for local dev.
- **CompletionProvider protocol.** One method: `complete(prompt, system) -> str`. Heuristic fallback for zero-LLM operation. Implemented in Phase 2.
- **Circle 4 storage:** SQLite (`anamnesis.db`). Same database will serve Circles 3 and 5. Episodes + turns tables with indexed queries.
- **Recency pipeline:** System-managed `_recency` bolus (inline, priority 25). FIFO. Budget carve-out configurable per agent (0–1000 tokens). Disabled by default.
- **System boluses:** IDs starting with `_` are system-managed. Excluded from user-facing list/delete. Participate in assembly.

## Build Order

Phase 1 (done): Circle 1 + Circle 2 (inject/ + bolus/ + config + API + CLI + dashboard)
Phase 2 (done): Circle 4 (episode capture + recency pipeline + CompletionProvider + agent API)
Phase 3 (next): Compilation pipeline (Circle 4 → Circle 3)
Phase 4: Reconciliation (Circle 3 → Circle 2)
Phase 5: Metrics
Phase 6: Circle 5 (behavioral mining)
Phase 7: Vector search (only if needed)

Pilot agents: Atlas (existing memories to migrate, Claude-based) and Selah (cold-start, local Gemma 4).

## Story Dependency Chain

**F01 (Phase 1):** S01 → S02 → S03 → S04 → S05 → S06 → S07 (all complete)
**F02 (Phase 2):** S01 → S02 → S03 → S04 (all complete)
**F03 (Phase 3):** Not yet scoped.

## Conventions

- PRDs follow the prd-creator skill format (F##/S## nomenclature). Templates in `/Users/hackstert/Atlas/.atlas/skills/prd-creator/references/`.
- The user is a physician-builder (MD/MPH) who values clinical analogies. The framework uses medical metaphors extensively (medication reconciliation, problem list, bolus).
- Prefer terse, direct communication. No trailing summaries.
- **Port assignments must be requested through Atlas before use.** Do not hardcode or assume port numbers. Create a request in `docs/request-port.md` and wait for Atlas CTO approval before configuring any service ports. See `docs/request-port.md` for the current assignments and the process.

## Assigned Ports

| Port | Service | Notes |
|------|---------|-------|
| 8741 | Anamnesis REST API | Production + dev |
| 5175 | Dashboard dev server | SvelteKit dev only |
| 4173 | Dashboard preview | SvelteKit preview only |
