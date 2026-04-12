# Anamnesis

A knowledge management framework for LLM agent systems. Library-first Python package that manages curated knowledge injection into any LLM via a single markdown file (`anamnesis.md`).

## Project State

- **S01 (scaffolding) and S02 (bolus system) are complete.** 36 tests passing. Package is installable via `uv sync`.
- **S03–S07 are in backlog.** S03 is next (anamnesis.md spec).
- **Knowledge directory:** `knowledge/anamnesis.md` (Circle 1) and `knowledge/boluses/` (Circle 2) live in this repo. This is the canonical knowledge store.

## Key Architecture Documents

- `docs/anamnesis/anamnesis-framework.md` — The full framework (five-circle model, triage questions, declarative/procedural/episodic knowledge, transport layer inversion, reconciliation model). ~1700 lines. This is the theory.
- `docs/anamnesis/anamnesis-construction.md` — The construction plan (Python library, package structure, API surface, build order). This is the implementation blueprint.
- `tasks/F01-circle-1-and-2-core.md` — Phase 1 PRD feature canvas. Circle 1 (injection) + Circle 2 (boluses).
- `tasks/F01-S01` through `F01-S07` — The seven implementation stories.
- `tasks/needed-features.md` — CLI, web dashboard, and agent onboarding design notes.

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
- **No CompletionProvider in Phase 1.** Deferred to Phase 3 (compilation pipeline).

## Build Order

Phase 1 (current): Circle 1 + Circle 2 (inject/ + bolus/ + config + API)
Phase 1b: CLI + agent onboarding (S06), web dashboard (S07)
Phase 2: Circle 4 (episode capture + recency pipeline to Circle 1, configurable token budget via slider)
Phase 3: Compilation pipeline (Circle 4 → Circle 3)
Phase 4: Reconciliation (Circle 3 → Circle 2)
Phase 5: Metrics
Phase 6: Circle 5 (behavioral mining)
Phase 7: Vector search (only if needed)

Pilot agents: Atlas (existing memories to migrate, Claude-based) and Selah (cold-start, local Gemma 4).

## Story Dependency Chain

S01 (scaffolding) → S02 (bolus system) → S03 (anamnesis.md spec) → S04 (injection assembly) → S05 (API layer) → S06 (CLI & agent onboarding) → S07 (web dashboard)

S01 and S02 are done. S03 is next. Each story depends on the prior.

## Conventions

- PRDs follow the prd-creator skill format (F##/S## nomenclature). Templates in `/Users/hackstert/Atlas/.atlas/skills/prd-creator/references/`.
- The user is a physician-builder (MD/MPH) who values clinical analogies. The framework uses medical metaphors extensively (medication reconciliation, problem list, bolus).
- Prefer terse, direct communication. No trailing summaries.
