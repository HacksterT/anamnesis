---
id: F02-S02
feature: F02
title: CompletionProvider Protocol
priority: Must-Have
status: done
created: 2026-04-12
type: software
---

# F02-S02: CompletionProvider Protocol

**Feature:** F02 — Circle 4 Episode Capture & Recency Pipeline
**Priority:** Must-Have

## Summary

Define and implement the `CompletionProvider` protocol — the abstraction that lets Anamnesis call any LLM for summarization without importing model-specific SDKs. This is the interface between Anamnesis (the knowledge framework) and the LLM (the intelligence). Phase 1 deferred this because no component needed LLM calls. Phase 2 needs it for auto-summarization of episodes into the recency slot. This story delivers the protocol, a heuristic fallback (no LLM needed), a static mock for testing, and a default summarization prompt template.

## Acceptance Criteria

- [x] `CompletionProvider` is a Python protocol with one method: `complete(prompt: str, system: str | None = None) -> str`
- [x] `HeuristicSummarizer` summarizes episodes without any LLM call — takes the last N turns, truncates to fit the token budget, returns a prose summary
- [x] `StaticCompletionProvider` returns canned responses for testing
- [x] A default summarization prompt template exists and is configurable
- [x] `KnowledgeConfig` accepts an optional `completion_provider` field
- [x] The summarizer function accepts an episode and a token budget, returns a summary string
- [x] The summarizer uses `CompletionProvider` if available, falls back to `HeuristicSummarizer`

## Tasks

### Backend

- [x] Create `src/anamnesis/completion/` package with:
  - `provider.py` — `CompletionProvider` protocol definition
  - `heuristic.py` — `HeuristicSummarizer` (no LLM, last N turns truncated)
  - `summarizer.py` — `summarize_episode(episode, budget, provider=None)` orchestrator
  - `prompts.py` — default summarization prompt template
  - `__init__.py` — public exports
- [x] Define `CompletionProvider` protocol:
  ```python
  @runtime_checkable
  class CompletionProvider(Protocol):
      def complete(self, prompt: str, system: str | None = None) -> str: ...
  ```
- [x] Implement `HeuristicSummarizer`:
  - Takes an episode's turns and a token budget
  - Strategy: take the last N turns that fit within the budget
  - Format: "Last session ({date}): {turn_1_content}... {turn_N_content}"
  - Truncate the oldest included turn if needed to fit budget
  - No LLM call — pure string manipulation with token counting
- [x] Implement `StaticCompletionProvider`:
  - Accepts a dict of prompt substrings → responses
  - Returns the matching response if any prompt key matches
  - Returns a default string otherwise
  - Used for testing the summarizer with predictable outputs
- [x] Implement `summarize_episode()`:
  - If `completion_provider` is provided: build prompt from template + episode turns, call provider, return result
  - If not: fall back to `HeuristicSummarizer`
  - Always respect the token budget — truncate the result if the provider returns too much
- [x] Write default summarization prompt template:
  ```
  Summarize this conversation session concisely. Focus on:
  - What was being worked on
  - Key decisions made
  - Open questions or next steps
  
  Keep the summary under {budget} tokens. Write in present tense, third person.
  
  Session:
  {turns}
  ```
- [x] Add `completion_provider` to `KnowledgeConfig`:
  ```python
  completion_provider: CompletionProvider | None = None
  ```
  Note: this field is not serializable to YAML — it's set programmatically by the application, not in the config file.

### Testing & Verification

- [x] Write test: `HeuristicSummarizer` produces output within token budget
- [x] Write test: `HeuristicSummarizer` with a 1-turn episode returns that turn's content
- [x] Write test: `HeuristicSummarizer` with a 50-turn episode takes only the last N that fit
- [x] Write test: `StaticCompletionProvider` returns canned responses
- [x] Write test: `summarize_episode` uses provider when available
- [x] Write test: `summarize_episode` falls back to heuristic when no provider
- [x] Write test: `summarize_episode` truncates provider output if it exceeds budget
- [x] Local Testing: `pytest tests/` passes

### Git

- [ ] Commit, fetch/rebase, push

## Technical Notes

- **One method.** The protocol has exactly one method: `complete(prompt, system) -> str`. No streaming, no tool use, no multi-turn, no model selection. The application wraps its LLM client to conform to this interface. Atlas wraps Claude. Selah wraps Gemma 4. The framework doesn't care.
- **Heuristic is the primary path.** For local models like Gemma 4, the heuristic may actually be preferable to a mediocre LLM summary. The heuristic is deterministic, fast, and free. LLM summarization is a quality upgrade, not a requirement.
- **The prompt template is a string, not a Jinja template.** Simple `{variable}` substitution. No template engine dependency.
- **CompletionProvider is not in the config file.** It's a runtime object, not a serializable setting. The application instantiates it and passes it to `KnowledgeConfig` or directly to the summarizer. The YAML config file has no `completion_provider` field.

## Blockers

- F02-S01 (Episode Storage) — depends on the `Episode` and `Turn` data models.
