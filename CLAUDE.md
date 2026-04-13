# Anamnesis

A knowledge management framework for LLM agent systems. Library-first Python package that manages curated knowledge injection into any LLM via a single markdown file (`anamnesis.md`).

## Project State

- **F01–F04 complete.** 251 tests passing.
- **Circles 1–4 implemented.** Circle 5 (behavioral mining) planned.
- **Dashboard:** SvelteKit app in `/dashboard` — bolus library, injection preview, Circle 3 curation queue, agent registry.
- **Knowledge directory:** `knowledge/anamnesis.md` (Circle 1) and `knowledge/boluses/` (Circle 2). Episodes + curation queue in SQLite (`anamnesis.db`).

## Key Architecture Documents

- `docs/anamnesis/anamnesis-framework.md` — Full framework theory (five-circle model, triage questions, knowledge types, reconciliation model).
- `docs/anamnesis/anamnesis-construction.md` — Implementation blueprint (package structure, design decisions, build order).
- `docs/anamnesis/anamnesis-roadmap.md` — Phase history, current state, what's next.
- `docs/anamnesis/anamnesis-agent-reference.md` — Full API reference for agents and developers.
- `tasks/needed-features.md` — Current gap list and backlog.
- `tasks/completed/` — Finished story files (audit trail of what was built and why).

## Design Decisions (Settled)

- **Injection format:** Markdown with `<knowledge>` XML wrapper. Not JSON, not YAML.
- **Circle 2 storage:** Markdown files with YAML frontmatter. Pluggable `BolusStore` interface.
- **Token budget:** 500 min / 4K soft max (configurable) / 6K hard ceiling.
- **Architecture:** Library-first. FastAPI is a thin wrapper.
- **Package manager:** uv (not pip).
- **No Docker for development.** `./start.sh` is sufficient.
- **API auth:** Optional API key via config. Unauthenticated by default.
- **CompletionProvider protocol:** `complete(prompt, system) -> str`. One method. No direct LLM imports in library code.
- **Circle 4 storage:** SQLite (`anamnesis.db`). Circles 3 and 4 share the same database.
- **System boluses:** IDs starting with `_` are system-managed. Excluded from user-facing list/delete.
- **Compilation is explicit.** Never runs automatically on `end_session()`. Triggered by `kf.compile()`, `anamnesis compile`, or `POST /v1/compile`.
- **Domain exceptions:** `BolusExistsError`, `BolusNotFoundError`, `CircleNotConfiguredError` — not bare `ValueError`/`KeyError`.

## Build Order

- F01 (done): Circle 1 + Circle 2 (bolus system, injection assembly, API, CLI, dashboard)
- F02 (done): Circle 4 (episode capture, recency pipeline, CompletionProvider, agent API)
- F03 (done): Per-agent profiles, injection routing, curation queue, compilation pipeline
- F04 (done): External content intake (upsert/append, Circle 3 dashboard)
- F05 (next): Reconciliation — permissiveness slider, auto-promote, contradiction detection
- F06: Dashboard UX — bolus editor, sort controls, batch curation
- F07: Circle 5 behavioral mining
- F08: Vector search (only if needed)

## Story Dependency Chain

**F01:** S01 → S02 → S03 → S04 → S05 → S06 → S07 (all complete)
**F02:** S01 → S02 → S03 → S04 (all complete)
**F03:** S01 → S02 → S03 → S04 → S05 (all complete)
**F04:** S01 → S02 → S03 (all complete)

## Conventions

- Story files use F##/S## nomenclature. Feature canvases first, then implementation stories.
- Prefer terse, direct communication. No trailing summaries.
- Tests live in `tests/`. One test file per module (`test_api.py`, `test_compile.py`, etc.).
- Run tests: `uv run pytest tests/ -q`
- Run linter: `uv run ruff check src/`

## Assigned Ports

| Port | Service |
|------|---------|
| 8741 | Anamnesis REST API |
| 5175 | Dashboard dev server (SvelteKit) |
| 4173 | Dashboard preview |
