---
id: F03-S04
feature: F03
title: Compilation Pipeline (Circle 4 → Circle 3)
priority: Must-Have
status: done
created: 2026-04-12
type: software
---

# F03-S04: Compilation Pipeline (Circle 4 → Circle 3)

**Feature:** F03 — Agent Profiles, Injection Routing & Compilation Pipeline
**Priority:** Must-Have

## Summary

Implement the compilation pipeline — the slow path from Circle 4 (episodes) to Circle 3 (curation queue). The pipeline reads uncompiled episodes, sends them to a `CompletionProvider` for fact extraction, and deposits the extracted facts in the curation queue with confidence scores. This is the first real analytical use of the LLM abstraction — beyond summarization, the model must identify durable knowledge worth promoting.

## Acceptance Criteria

- [x] `kf.compile()` processes all episodes where `compiled = FALSE`
- [x] Each episode is sent to the `CompletionProvider` with an extraction prompt
- [x] Extracted facts are deposited in the Circle 3 curation queue via `kf.stage()`
- [x] Each extracted fact includes: the fact text, source episode ID, suggested target bolus, and a confidence score
- [x] After compilation, the episode is marked `compiled = TRUE` in SQLite
- [x] A default extraction prompt template exists and is configurable
- [x] `kf.compile()` with no `CompletionProvider` raises a clear error (no heuristic fallback — extraction requires an LLM)
- [x] CLI: `anamnesis compile [--agent <name>]` runs the pipeline
- [x] REST: `POST /v1/compile` triggers compilation
- [x] Compilation results are logged: episodes processed, facts extracted, errors

## Tasks

### Backend

- [x] Create `src/anamnesis/compile/` package with:
  - `pipeline.py` — `compile_episodes(store, episode_store, curation_store, provider, prompt=None)` orchestrator
  - `extractor.py` — `extract_facts(episode, provider, prompt) -> list[ExtractedFact]` single-episode extraction
  - `prompts.py` — default extraction prompt template
  - `__init__.py` — public exports
- [x] Implement `ExtractedFact` dataclass
- [x] Implement extraction prompt template (includes existing bolus list, truncates long turns)
- [x] Implement `extract_facts()`: build prompt, call provider, parse JSON response, return list
- [x] Implement `compile_episodes()`: query uncompiled → extract → stage → mark compiled
- [x] Wire `KnowledgeFramework.compile(agent=None)` method
- [x] Add `POST /v1/compile` endpoint (accepts optional `agent` param)
- [x] Add `anamnesis compile [--agent <name>]` CLI command
- [x] Add `compiled` flag update to `EpisodeStore` (method to mark compiled)
- [x] Add `completion_provider` config fields + YAML flattening in config_loader
- [x] `OpenAICompatibleProvider` (httpx, Ollama-compatible) in `completion/openai_compat.py`

### Testing & Verification

- [x] Write test: compile processes uncompiled episodes using `StaticCompletionProvider`
- [x] Write test: extracted facts appear in curation queue
- [x] Write test: compiled episodes are marked `compiled = TRUE`
- [x] Write test: already-compiled episodes are skipped
- [x] Write test: compile with no provider raises error
- [x] Write test: compile with agent filter processes only that agent's episodes
- [x] Write test: malformed LLM output is handled gracefully (logged, not crashed)
- [x] Write test: REST endpoint triggers compilation
- [x] Local Testing: 251 tests passing (`uv run pytest tests/ -q`)

### Git

- [x] Commit: `a9bffb7 F03-S01+S02: Per-agent profiles, injection routing, recency isolation`

## Technical Notes

- **No heuristic fallback.** Unlike recency summarization (which has a last-N-turns heuristic), fact extraction requires an LLM. The heuristic can't identify what's worth keeping vs what's noise. `compile()` without a `CompletionProvider` is an error, not a degraded mode.
- **JSON output from the LLM.** The extraction prompt asks for JSON. LLMs sometimes return malformed JSON or extra text. The parser should handle: valid JSON, JSON wrapped in markdown code blocks, and graceful failure for unparseable responses.
- **Existing bolus list in the prompt.** The extraction prompt includes the current bolus manifest so the LLM can suggest routing facts to existing boluses rather than always creating new ones.
- **Confidence scores are LLM-estimated.** They're useful for queue ordering but not for auto-promotion decisions (that's Phase 4's permissiveness slider). In this phase, every fact requires human confirmation regardless of confidence.
- **Compilation cost.** Each episode sent to the LLM costs tokens. For a 20-turn episode, the extraction prompt + response might be 3-5K tokens. At Claude Haiku pricing, that's fractions of a cent per episode. For Gemma 4 locally, it's free but slower.

## Blockers

- F03-S03 (Circle 3 Schema) — depends on the curation queue for depositing extracted facts.
- F02-S02 (CompletionProvider) — depends on the protocol for LLM calls.
