---
id: F01-S03
feature: F01
title: anamnesis.md Specification
priority: Must-Have
status: backlog
created: 2026-04-12
type: software
---

# F01-S03: anamnesis.md Specification

**Feature:** F01 — Circle 1 & Circle 2 Core
**Priority:** Must-Have

## Summary

Define the specification for `anamnesis.md` — the single knowledge injection file that is Circle 1. This story produces the canonical document structure, section definitions, formatting rules, length bounds, and a reference example. The spec is both a human-readable document (for anyone configuring the system) and a machine-enforceable contract (the assembler in S04 generates files that conform to it). This is the most important design artifact in Phase 1: every LLM that consumes Anamnesis knowledge reads this format.

## Acceptance Criteria

- [ ] A specification document exists at `docs/anamnesis/anamnesis-md-spec.md` defining the format
- [ ] The spec defines all sections, their ordering, their purpose, and whether they are required or optional
- [ ] The spec defines the `<knowledge>` XML outer wrapper and its role
- [ ] The spec defines optimal length bounds with clear thresholds and consequences:
  - Minimum viable: ~500 tokens
  - Target sweet spot: 1,000–2,500 tokens
  - Soft maximum: 4,000 tokens (configurable, default)
  - Hard ceiling: 6,000 tokens
- [ ] The spec includes a complete reference example of a well-formed `anamnesis.md`
- [ ] The spec defines the bolus manifest line format (how active boluses appear in the Knowledge Domains section)
- [ ] A Python dataclass or typed dict defines the section schema programmatically in `src/anamnesis/inject/schema.py`
- [ ] The schema is importable and usable by the assembler (S04) for validation

## Tasks

### Backend

- [ ] Write the `anamnesis.md` format specification document at `docs/anamnesis/anamnesis-md-spec.md`. The spec must define:

  **Document structure:**
  ```
  <knowledge>
  # Identity
  {narrative prose — who the agent is, who the user is, orientation context}

  # Knowledge Domains
  {bolus manifest — one line per active bolus: name, summary, pointer}

  # Capabilities
  {skill manifest — one line per skill: name, description, triggers}
  {Optional — omitted if agent has no registered skills}

  # Current Context
  {recency context — what happened recently, open threads, active work}
  {Optional — omitted if no recency data available}

  # Constraints
  {behavioral rules — what the agent must not do, how to qualify uncertain info}
  </knowledge>
  ```

  **Section definitions:**

  | Section | Required | Content Type | Purpose |
  |---------|----------|-------------|---------|
  | Identity | Yes | Narrative prose | Orient the LLM to the user/agent identity. Who, what, primary context. |
  | Knowledge Domains | Yes | Structured list | Manifest of active boluses. Each entry: bolus name, one-line summary, retrieval pointer (bolus ID). |
  | Capabilities | No | Structured list | Skill manifest. Each entry: skill name, description, trigger keywords. Omitted if no skills registered. |
  | Current Context | No | Narrative prose | Recency context compiled from recent sessions. Omitted until Circle 4 compilation is implemented (Phase 3+). |
  | Constraints | No | Rule list | Behavioral boundaries. Omitted if none configured. |

  **Bolus manifest line format:**
  ```
  - **{title}**: {summary} -> `{bolus_id}`
  ```
  Example:
  ```
  - **Infrastructure**: Mac Mini M4 Pro, macdevserver (Ubuntu), home network. -> `infrastructure`
  ```
  The `-> \`{bolus_id}\`` pointer is what the agent uses to call `retrieve(bolus_id)` when it needs the full content.

  **Length bounds:**

  | Threshold | Tokens | Meaning |
  |-----------|--------|---------|
  | Minimum viable | ~500 | Below this, the agent lacks sufficient orientation. Identity section alone should approach this. |
  | Target sweet spot | 1,000–2,500 | Full identity, 10-15 active boluses in manifest, skill manifest, recency, constraints. Highest signal-per-token ratio. |
  | Soft maximum | 4,000 | Configurable via `circle1_max_tokens`. Beyond this, the injection consumes meaningful context budget. The assembler warns but does not truncate. |
  | Hard ceiling | 6,000 | The assembler refuses to generate. If above 6K tokens, Circle 2 content has leaked into Circle 1 — the manifest has become the content. Recuate: demote detail to boluses, tighten summaries. |

- [ ] Write the complete reference example as part of the spec doc:
  ```markdown
  <knowledge>
  # Identity
  Physician-builder. Solo operator. Primary stack: Python and TypeScript.
  Building AI agent infrastructure (Anamnesis, Atlas) and a career intelligence
  platform (Cortivus). Mac Mini M4 Pro as primary development machine.

  # Knowledge Domains
  - **Infrastructure**: Mac Mini M4 Pro, macdevserver (Ubuntu), home network topology. -> `infrastructure`
  - **Technical Skills**: Python, TypeScript, LangGraph, FastAPI, SQLite, Next.js. -> `technical-skills`
  - **Projects**: Anamnesis (knowledge framework), Atlas (personal assistant), Cortivus (career platform). -> `projects`
  - **Credentials**: MD, MPH, Google Cloud certificate. -> `credentials`
  - **Subscriptions**: 12 active services — GitHub, Anthropic, Vercel, etc. -> `subscriptions`

  # Capabilities
  - Manage Email: read, compose, reply, organize. Triggers: email, message, send, draft.
  - Schedule: check availability, book, reschedule. Triggers: schedule, appointment, calendar.

  # Current Context
  Last session: working on anamnesis framework Phase 1 PRD. Decided on markdown
  format with <knowledge> wrapper for injection. Storage decision: markdown files
  for Circle 2 boluses. Open thread: token counting strategy (tiktoken vs pluggable).

  # Constraints
  - Do not hallucinate credentials or certifications. If uncertain, ask.
  - Qualify unconfirmed facts with provenance: "Based on a prior conversation..."
  - Do not store secrets, API keys, or tokens in any knowledge layer.
  </knowledge>
  ```

- [ ] Create `src/anamnesis/inject/schema.py` defining the section schema programmatically:
  ```python
  @dataclass
  class InjectionSection:
      name: str               # Section header (e.g., "Identity")
      required: bool          # Must be present in every injection
      content_type: str       # "narrative" | "structured_list" | "rule_list"
      order: int              # Position in the document (1-indexed)

  INJECTION_SCHEMA: list[InjectionSection] = [
      InjectionSection("Identity", required=True, content_type="narrative", order=1),
      InjectionSection("Knowledge Domains", required=True, content_type="structured_list", order=2),
      InjectionSection("Capabilities", required=False, content_type="structured_list", order=3),
      InjectionSection("Current Context", required=False, content_type="narrative", order=4),
      InjectionSection("Constraints", required=False, content_type="rule_list", order=5),
  ]
  ```

- [ ] Define token budget constants in the schema module:
  ```python
  TOKEN_MINIMUM_VIABLE = 500
  TOKEN_TARGET_LOW = 1000
  TOKEN_TARGET_HIGH = 2500
  TOKEN_SOFT_MAX_DEFAULT = 4000
  TOKEN_HARD_CEILING = 6000
  ```

### Testing & Verification

- [ ] Write test: validate the reference example against the schema (correct sections in correct order, required sections present)
- [ ] Write test: a document missing the Identity section fails validation
- [ ] Write test: a document missing Knowledge Domains section fails validation
- [ ] Write test: a document with sections out of order is flagged
- [ ] Local Testing: `pytest tests/` passes
- [ ] Manual Testing: CHECKPOINT — Notify user to review the spec document and reference example for accuracy and completeness

### Git

- [ ] Commit, fetch/rebase, push

## Technical Notes

- **The spec is a design document AND a code artifact.** The markdown spec in `docs/` is for humans. The schema in `inject/schema.py` is for the assembler. Both must stay in sync. The spec doc is the source of truth; the code implements it.
- **The `<knowledge>` wrapper.** This is the one place XML earns its keep in the injection. It tells the LLM "this block is injected knowledge, not conversation or system instructions." Everything inside is markdown. The wrapper is not a section — it wraps the entire document.
- **Section ordering is fixed.** Identity first (orient), Knowledge Domains second (what's available), Capabilities third (what the agent can do), Current Context fourth (what's happening now), Constraints last (boundaries). This ordering is deliberate: the LLM reads top-to-bottom, and the most stable sections (identity, domains) come first for cache friendliness.
- **The manifest line format.** The `-> \`bolus_id\`` pointer convention uses backtick-wrapped IDs so the LLM can unambiguously extract the bolus ID for retrieval calls. The format is designed to be parseable by both humans and a simple regex.
- **Length bounds are advisory, not all hard stops.** The minimum is a design guideline. The soft max triggers a warning. Only the hard ceiling prevents generation. This gives the human curation latitude while flagging when the injection is growing beyond its design envelope.

## Blockers

- F01-S01 (Project Scaffolding) — depends on package structure for `inject/schema.py` placement.
