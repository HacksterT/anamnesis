---
id: F01
title: Circle 1 & Circle 2 Core
status: draft
created: 2026-04-12
---

# F01: Circle 1 & Circle 2 Core

## Overview

**Feature:** Anamnesis Phase 1 — Circle 1 (Injection Assembly) + Circle 2 (Bolus System)
**Problem:** There is no LLM-agnostic, framework-level solution for managing curated knowledge injection into agent systems. Existing approaches either hardcode knowledge into system prompts, scatter it across multiple injection files, or store everything and hope retrieval sorts it out. The result is brittle, uncurated, and model-specific.
**Goal:** A working Python library and REST API that assembles a single, curated `anamnesis.md` knowledge injection file from a managed library of knowledge boluses. Any LLM system can call the API to get the knowledge prompt. Boluses are markdown files with frontmatter — human-readable, git-friendly, and curation-first.

## Context

Anamnesis is a knowledge management framework built on a five-circle trust model. The framework and construction documents describe the full architecture across all five circles, but the build order is deliberate: start from the center (Circle 1 — injection) and work outward (Circle 4 — episodes, Circle 5 — behavioral mining). Phase 1 validates the two highest-confidence, highest-value layers.

Circle 1 is the single injection point — one markdown file (`anamnesis.md`) loaded into the LLM's context window on every turn. Circle 2 is the confirmed knowledge library — structured boluses retrieved on demand. Together they establish the core loop: boluses are curated in Circle 2, a manifest of active boluses is assembled into Circle 1, and the LLM consumes the injection.

This phase also establishes the library-first architecture (Python library as the core, FastAPI as a thin wrapper) and the bolus activation model (not all boluses appear in every injection — selective toggles enable niche agents and future dynamic assembly).

The curation UI for human reconciliation is explicitly out of scope and will be its own PRD.

## Stories

| ID | Title | Priority | Status |
|----|-------|----------|--------|
| F01-S01 | Project Scaffolding & Configuration | Must-Have | Backlog |
| F01-S02 | Bolus System (Circle 2) | Must-Have | Backlog |
| F01-S03 | anamnesis.md Specification | Must-Have | Backlog |
| F01-S04 | Injection Assembly (Circle 1) | Must-Have | Backlog |
| F01-S05 | REST API Layer | Must-Have | Backlog |

## Non-Goals

- **Circle 3 (Curation Layer).** No reconciliation queue, no staging area for unconfirmed facts. Phase 1 assumes all knowledge is human-curated ground truth.
- **Circle 4 (Episode Capture).** No transcript logging, no raw episode storage. Compilation pipeline is a later phase.
- **Circle 5 (Behavioral Mining).** No observation pipelines, no behavioral pattern detection.
- **Compilation Pipeline.** No LLM-driven extraction from episodes. The `CompletionProvider` interface is deferred until Phase 3 when compilation needs it.
- **Curation UI.** No dashboard, no reconciliation interface, no web frontend. The library provides data and operations; the UI is a separate PRD.
- **Vector Search.** No embeddings, no semantic similarity. Circle 2 retrieval is categorical pointer lookup on markdown files.
- **Permissiveness Slider.** No configurable trust levels for agent autonomy. Deferred to Phase 4 (reconciliation).
- **Dynamic Manifest Assembly.** Phase 1 uses static activation toggles. Context-aware dynamic routing of boluses is a future capability. The bolus metadata schema supports it; the assembly logic does not implement it yet.

## Dependencies

- Python 3.11+ (for modern dataclass features and Path handling)
- FastAPI + Uvicorn (for the API layer — S05)
- tiktoken or equivalent (for token counting — model-agnostic tokenizer selection TBD)
- No external database dependencies. Storage is the local filesystem (markdown files).

## Success Metrics

- A consumer can call `GET /v1/knowledge/injection` and receive a well-formed `anamnesis.md` markdown document
- Boluses can be created, read, updated, deleted, listed, and toggled active/inactive via both the Python API and REST endpoints
- The assembled `anamnesis.md` respects the configured token budget and only includes active boluses
- The library can be imported and configured by an external application with a single `KnowledgeConfig` object
- All bolus files are human-readable markdown with frontmatter, editable in any text editor or Obsidian

## Design Decisions (Resolved)

- **Token counting strategy.** Pluggable. A `TokenCounter` protocol with one method (`count(text) -> int`). Ships with a simple word-based heuristic (`words * 1.3`) as the zero-dependency default. Users plug in model-specific tokenizers (tiktoken for GPT, Anthropic's counter for Claude, etc.) when they need precision. The budget thresholds are advisory, so the default heuristic is sufficient for guardrail enforcement.
- **Bolus frontmatter schema.** Defined in S02, revised in S03. Required fields: `id`, `title`, `active`, `render`, `summary`, `created`, `updated`. Optional fields: `priority`, `tags`. The `render` field (`inline` | `reference`) controls how the bolus appears in the injection. The `priority` field controls ordering. Unknown fields are preserved on round-trip for future extensibility.
- **API authentication.** Optional API key via config (`api_key` field in `KnowledgeConfig`). If set, all `/v1/` routes require `Authorization: Bearer {key}`. If not set, no auth required. Unauthenticated by default for local development.

---

*Created: 2026-04-12*
