---
id: F01-S04
feature: F01
title: Injection Assembly (Circle 1)
priority: Must-Have
status: backlog
created: 2026-04-12
type: software
---

# F01-S04: Injection Assembly (Circle 1)

**Feature:** F01 — Circle 1 & Circle 2 Core
**Priority:** Must-Have

## Summary

Implement the Circle 1 injection assembler — the process that reads active boluses from Circle 2, reads configured section content, and assembles the single `anamnesis.md` injection file. This is the core value delivery of Phase 1: a caller (human, API consumer, or LLM system) gets a well-formed, token-budgeted knowledge injection document. The assembler enforces the spec from S03, respects the activation toggles from S02, and implements token budget enforcement with warning/refusal thresholds.

## Acceptance Criteria

- [ ] `kf.get_injection()` returns a string containing a well-formed `anamnesis.md` document wrapped in `<knowledge>` tags
- [ ] The assembled document includes only active boluses in the Knowledge Domains manifest
- [ ] The assembled document respects section ordering defined in the schema (Identity, Knowledge Domains, Capabilities, Current Context, Constraints)
- [ ] Optional sections with no content are omitted cleanly (no empty headers)
- [ ] `kf.get_injection()` raises a warning (logged, not exception) when the assembled document exceeds the configured `circle1_max_tokens`
- [ ] `kf.get_injection()` raises an error when the assembled document exceeds the hard ceiling (6,000 tokens)
- [ ] `kf.assemble()` writes the assembled content to the configured `circle1_path` file
- [ ] `kf.get_injection_metrics()` returns token count, section breakdown, active bolus count, and budget utilization percentage
- [ ] Token counting is pluggable — default implementation provided, alternative tokenizers can be swapped via config
- [ ] The Identity section content is read from a configurable source (a file path or a string in config)

## Tasks

### Backend

- [ ] Implement token counting in `inject/budget.py`:
  - Define `TokenCounter` protocol: `count(text: str) -> int`
  - Implement `SimpleTokenCounter` — word-based heuristic (words × 1.3) as zero-dependency default
  - Implement `TiktokenCounter` — wraps tiktoken with configurable model/encoding (optional dependency)
  - `KnowledgeConfig` gets a `token_counter: str = "simple"` field (`"simple"` | `"tiktoken"`)
  - Budget enforcement: `check_budget(text, soft_max, hard_ceiling) -> BudgetResult` returning status (ok/warning/exceeded) and counts

- [ ] Implement the assembler in `inject/assembler.py`:
  - `assemble(config, bolus_store, sections) -> str` — the pure function that builds the document
  - Assembly process:
    1. Read Identity content from `config.identity_source` (file path or inline string)
    2. Query `bolus_store.list(active_only=True)` for active boluses
    3. Generate Knowledge Domains section: one manifest line per active bolus using `summary` and `id` from frontmatter
    4. Read Capabilities section from `config.capabilities_source` (file path, inline string, or None)
    5. Read Current Context from `config.recency_source` (file path, inline string, or None)
    6. Read Constraints from `config.constraints_source` (file path, inline string, or None)
    7. Assemble sections in schema order, skip None/empty optional sections
    8. Wrap in `<knowledge>` tags
    9. Run token budget check; log warning or raise on ceiling breach
    10. Return assembled string

- [ ] Add section source fields to `KnowledgeConfig`:
  ```python
  # Section content sources (file path or inline string)
  identity_source: Path | str = ""          # Required for valid assembly
  capabilities_source: Path | str | None = None   # Optional
  recency_source: Path | str | None = None        # Optional (Phase 3+ populates this)
  constraints_source: Path | str | None = None     # Optional
  ```

- [ ] Implement `KnowledgeFramework.get_injection() -> str`:
  - Calls the assembler
  - Returns the assembled markdown string (for API consumers and direct library use)

- [ ] Implement `KnowledgeFramework.assemble() -> Path`:
  - Calls the assembler
  - Writes the result to `config.circle1_path`
  - Returns the path written to

- [ ] Implement `KnowledgeFramework.get_injection_metrics() -> dict`:
  ```python
  {
      "total_tokens": 1847,
      "soft_max": 4000,
      "hard_ceiling": 6000,
      "utilization_pct": 46.2,
      "status": "ok",  # "ok" | "warning" | "exceeded"
      "active_boluses": 5,
      "total_boluses": 8,
      "sections": {
          "Identity": {"tokens": 312, "present": True},
          "Knowledge Domains": {"tokens": 485, "present": True},
          "Capabilities": {"tokens": 210, "present": True},
          "Current Context": {"tokens": 0, "present": False},
          "Constraints": {"tokens": 140, "present": True},
      }
  }
  ```

- [ ] Implement manifest line generation:
  - For each active bolus, read its `title`, `summary`, and `id` from metadata
  - Format: `- **{title}**: {summary} -> \`{id}\``
  - Sort by: configurable (alphabetical by title as default, or explicit ordering field in frontmatter)

### Dependencies (if new packages added)

- [ ] tiktoken is an optional dependency (only needed if `token_counter: "tiktoken"` is configured). Add to `[project.optional-dependencies]` under a `tiktoken` group, not as a core requirement.
- [ ] Audit tiktoken: check weekly downloads, last publish date, known advisories
- [ ] Document in Technical Notes

### Testing & Verification

- [ ] Write test: assemble with 5 active boluses produces valid document with correct section order
- [ ] Write test: assemble with 0 active boluses still produces valid document (empty Knowledge Domains section with no entries)
- [ ] Write test: inactive boluses are excluded from manifest
- [ ] Write test: optional sections with None content are omitted (no empty `# Capabilities` header)
- [ ] Write test: document exceeding soft max logs warning but succeeds
- [ ] Write test: document exceeding hard ceiling raises error
- [ ] Write test: `get_injection_metrics()` returns correct token counts and utilization
- [ ] Write test: section sources work as both file paths and inline strings
- [ ] Write test: manifest lines are correctly formatted with pointer syntax
- [ ] Local Testing: `pytest tests/` passes, all acceptance criteria verified
- [ ] Manual Testing: CHECKPOINT — Notify user to review assembled anamnesis.md output for formatting, readability, and correctness

### Git

- [ ] Commit, fetch/rebase, push

## Technical Notes

- **The assembler is a pure function.** `assemble()` takes config, store, and section data as inputs and returns a string. No side effects. `KnowledgeFramework.assemble()` wraps it with the file-write side effect. `KnowledgeFramework.get_injection()` wraps it without the file write. This makes the core logic testable without filesystem interaction.
- **Section sources are flexible.** Each section can come from a file path (read at assembly time) or an inline string (provided in config). File paths support the "edit your identity in a text file" workflow. Inline strings support programmatic configuration. The assembler resolves both transparently.
- **Token counting is approximate and that's fine.** The simple heuristic (words × 1.3) is within 10-15% of actual token counts for English prose. The budget thresholds are advisory guidelines, not byte-exact limits. Precision matters less than having the guardrails at all.
- **Manifest ordering.** Default is alphabetical by bolus title. A future enhancement could add an `order` field to bolus frontmatter for explicit positioning. The assembler should be written to support a sort key without hardcoding alphabetical.
- **The `<knowledge>` wrapper is added by the assembler, not stored in any source file.** Section content files contain raw markdown. The assembler adds the wrapper during assembly. This keeps the source files clean and the wrapper as an assembly concern.

## Blockers

- F01-S01 (Project Scaffolding) — depends on `KnowledgeConfig` and `KnowledgeFramework` shell.
- F01-S02 (Bolus System) — depends on `BolusStore.list()` and bolus metadata access.
- F01-S03 (anamnesis.md Spec) — depends on schema definition and section ordering.
