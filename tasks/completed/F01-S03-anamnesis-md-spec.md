---
id: F01-S03
feature: F01
title: anamnesis.md Specification
priority: Must-Have
status: done
created: 2026-04-12
type: software
---

# F01-S03: anamnesis.md Specification

**Feature:** F01 — Circle 1 & Circle 2 Core
**Priority:** Must-Have

## Summary

Define the specification for `anamnesis.md` — the single knowledge injection file that is Circle 1. This story produces the canonical document format, the render model (inline vs reference), the bolus manifest line format, the `retrieve_knowledge` tool contract, length bounds, and a reference example. The spec is both a human-readable document (for anyone configuring the system) and a machine-enforceable contract (the assembler in S04 generates files that conform to it).

## Design Decisions

The injection format was simplified during implementation based on a key insight: **everything is a knowledge bolus**. Identity, skills, constraints, behavioral insights, and context are all boluses — not hardcoded sections. The bolus `render` field (`inline` vs `reference`) and `priority` field control how and where content appears in the injection. Tags handle categorization. No hardcoded section schema exists.

This means:
- No `InjectionSection` dataclass or fixed section ordering
- No section content sources in config (identity_source, constraints_source, etc.)
- The injection structure emerges from active boluses and their metadata
- Adding a new "kind" of knowledge is just creating a bolus with a tag — no schema change

## Acceptance Criteria

- [x] A specification document exists at `docs/anamnesis/anamnesis-md-spec.md` defining the format
- [x] The spec defines the `<knowledge>` XML outer wrapper and its role
- [x] The spec defines the two render modes (`inline` and `reference`) and when to use each
- [x] The spec defines the bolus manifest line format for reference boluses
- [x] The spec defines the `retrieve_knowledge` tool contract for agent frameworks
- [x] The spec defines optimal length bounds with clear thresholds and consequences
- [x] The spec includes complete reference examples (coding mode and philosophy mode)
- [x] A Python module at `src/anamnesis/inject/schema.py` defines render mode constants, token budget constants, the `retrieve_knowledge` tool definition, and a `validate_injection()` function
- [x] The schema module is importable and usable by the assembler (S04)

## Tasks

### Backend

- [x] Write the `anamnesis.md` format specification document at `docs/anamnesis/anamnesis-md-spec.md`. The spec defines:

  **Core model — one primitive, two render modes:**

  Every knowledge bolus has a `render` field:
  - `inline` — full content rendered directly in the injection. For content the agent must absorb immediately (identity, constraints, behavioral rules).
  - `reference` — summary line with a retrieval pointer. For content the agent looks up on demand (detailed knowledge, expertise, project specs).

  **Document structure:**
  ```
  <knowledge>
  {inline boluses rendered as prose, ordered by priority}

  ## Available Knowledge
  {reference boluses as manifest lines, ordered by priority then alphabetically}
  </knowledge>
  ```

  **Bolus frontmatter schema:**
  ```yaml
  ---
  id: infrastructure              # Required. Unique slug identifier.
  title: Infrastructure            # Required. Human-readable display name.
  active: true                     # Required. Activation toggle.
  render: reference                # Required. "inline" or "reference".
  priority: 50                     # Optional. Ordering (lower = earlier). Default: 50.
  summary: "Mac Mini M4 Pro, macdevserver, home network."
                                   # Required. One-line summary.
  tags: [technical, hardware]      # Optional. Free-form categorization.
  created: 2026-04-12              # Required. ISO date.
  updated: 2026-04-12              # Required. ISO date.
  ---
  ```

  **Suggested priority ranges:**
  - 1–20: Identity and orientation
  - 21–40: Context and recency
  - 41–70: Knowledge and skills (default: 50)
  - 71–89: Behavioral insights
  - 90–100: Constraints and rules

  **Reference manifest line format:**
  ```
  - **{title}**: {summary} -> `{bolus_id}`
  ```
  The `-> \`{bolus_id}\`` pointer is what the agent uses to call `retrieve_knowledge(bolus_id)`.

  **Length bounds:**

  | Threshold | Tokens | Meaning |
  |-----------|--------|---------|
  | Minimum viable | ~500 | Below this, the agent lacks sufficient orientation. |
  | Target sweet spot | 1,000–2,500 | Full identity, 10–15 reference boluses in manifest, constraints. Highest signal-per-token ratio. |
  | Soft maximum | 4,000 | Configurable via `circle1_max_tokens`. Assembler warns but does not truncate. |
  | Hard ceiling | 6,000 | Assembler refuses to generate. Too much inline content — demote to reference boluses. |

- [x] Write reference examples showing the same system in different modes (coding vs philosophy) to demonstrate dynamic bolus activation.

- [x] Define the `retrieve_knowledge` tool contract — a standardized tool definition that works as a Claude tool, OpenAI function, or MCP tool:
  ```json
  {
    "name": "retrieve_knowledge",
    "description": "Retrieve the full content of a knowledge bolus by ID.",
    "parameters": {
      "type": "object",
      "properties": {
        "bolus_id": {
          "type": "string",
          "description": "The bolus identifier from the knowledge manifest"
        }
      },
      "required": ["bolus_id"]
    }
  }
  ```

- [x] Create `src/anamnesis/inject/schema.py` with:
  - Render mode constants (`RENDER_INLINE`, `RENDER_REFERENCE`)
  - Token budget constants (`TOKEN_MINIMUM_VIABLE` through `TOKEN_HARD_CEILING`)
  - `RETRIEVE_KNOWLEDGE_TOOL` dict (the standard tool definition)
  - `validate_injection()` function checking `<knowledge>` wrapper and non-empty content

### Testing & Verification

- [x] Write tests: render mode constants, token budget ordering, tool definition structure
- [x] Write tests: validation passes for well-formed documents, fails for missing wrapper, fails for empty content
- [x] Local Testing: `pytest tests/` passes
- [x] Manual Testing: CHECKPOINT — User reviewed spec and render model design

### Git

- [ ] Commit, fetch/rebase, push

## Technical Notes

- **The spec is a design document AND a code artifact.** The markdown spec in `docs/` is for humans. The schema module in `inject/schema.py` is for the assembler. Both must stay in sync.
- **The `<knowledge>` wrapper.** Tells the LLM "this block is injected knowledge, not conversation or system instructions." Everything inside is markdown.
- **The manifest line format.** The `-> \`bolus_id\`` pointer convention uses backtick-wrapped IDs so the LLM can unambiguously extract the bolus ID for `retrieve_knowledge` calls.
- **Length bounds are advisory, not all hard stops.** The minimum is a design guideline. The soft max triggers a warning. Only the hard ceiling prevents generation.
- **No hardcoded sections.** The original design had five fixed sections (Identity, Knowledge Domains, Capabilities, Current Context, Constraints). This was simplified to the render model during implementation — all content types are boluses with `render` and `priority` metadata. The injection structure emerges from the data.

## Blockers

- F01-S01 (Project Scaffolding) — depends on package structure for `inject/schema.py` placement.
