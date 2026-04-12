# anamnesis.md Format Specification

The canonical format for Circle 1 knowledge injection files. Every LLM that consumes Anamnesis knowledge reads this format.

---

## Core Model

There is one primitive: the **knowledge bolus**. Everything — identity, facts, skills, constraints, behavioral insights, context — is a bolus. The injection file is assembled from active boluses.

Each bolus has a `render` mode that controls how it appears in the injection:

| Render Mode | Behavior | Use When |
|-------------|----------|----------|
| `inline` | Full content rendered directly in the injection | Agent must absorb this immediately — identity, constraints, behavioral rules |
| `reference` | Summary line with retrieval pointer | Agent looks this up on demand — detailed knowledge, expertise, project specs |

Tags (free-form) handle categorization. Priority (integer) controls ordering. The assembler doesn't care *what kind* of knowledge a bolus contains — only whether to render it inline or as a reference pointer.

---

## Document Structure

```
<knowledge>
{inline boluses rendered as prose, ordered by priority}

## Available Knowledge
{reference boluses as manifest lines, ordered by priority then alphabetically}
</knowledge>
```

The `<knowledge>` XML wrapper tells the LLM "this block is injected knowledge, not conversation or system instructions." Everything inside is markdown.

The `## Available Knowledge` header only appears if there are active reference boluses. Inline boluses render as prose with no header — they flow naturally at the top of the document.

If there are no inline boluses, the document starts directly with the Available Knowledge section.

---

## Bolus Frontmatter Schema

Every bolus is a markdown file with YAML frontmatter:

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

Full bolus content here. This is what gets rendered inline
or returned when the agent calls retrieve_knowledge("infrastructure").
```

### Suggested Tag Conventions

Tags are free-form, but these conventions help with UI grouping and filtering:

- `identity` — orientation, who/what the agent or user is
- `knowledge` — factual information (default for most boluses)
- `skill` — capabilities, what the agent can do
- `constraint` — behavioral boundaries and rules
- `behavioral` — Circle 5 insights, preferences, communication patterns
- `context` — recency, current state, active work
- `persona` — expert personas (patient safety, AI memory, etc.)

### Suggested Priority Ranges

| Range | Use |
|-------|-----|
| 1–20 | Identity and orientation |
| 21–40 | Context and recency |
| 41–70 | Knowledge and skills (default: 50) |
| 71–89 | Behavioral insights |
| 90–100 | Constraints and rules |

---

## Reference Manifest Line Format

Each active reference bolus appears as one line in the Available Knowledge section:

```
- **{title}**: {summary} -> `{bolus_id}`
```

Example:

```
- **Infrastructure**: Mac Mini M4 Pro, macdevserver, home network. -> `infrastructure`
- **Technical Skills**: Python, TypeScript, LangGraph, FastAPI. -> `technical-skills`
```

The `-> \`{bolus_id}\`` pointer is what the agent uses to call `retrieve_knowledge(bolus_id)` to get the full content. The backtick-wrapped ID is parseable by both humans and a simple regex.

Reference entries are sorted by priority, then alphabetically by title within the same priority.

---

## Retrieval Contract

The injection file tells the agent what knowledge is available. When the agent needs the full content of a reference bolus, it calls the `retrieve_knowledge` tool:

```json
{
  "name": "retrieve_knowledge",
  "description": "Retrieve the full content of a knowledge bolus by ID. Use when you need details beyond what the summary in your knowledge prompt provides.",
  "parameters": {
    "type": "object",
    "properties": {
      "bolus_id": {
        "type": "string",
        "description": "The bolus identifier from the knowledge manifest (e.g. 'infrastructure')"
      }
    },
    "required": ["bolus_id"]
  }
}
```

This tool definition works as a Claude tool, OpenAI function, or MCP tool. The application registers it with whatever agent framework it uses. The handler calls `kf.retrieve(bolus_id)` and returns the bolus content.

The retrieval happens within the same conversation turn — the bolus content lands in context as a tool result, available for the rest of the conversation.

---

## Length Bounds

| Threshold | Tokens | Meaning |
|-----------|--------|---------|
| Minimum viable | ~500 | Below this, the agent lacks sufficient orientation. |
| Target sweet spot | 1,000–2,500 | Full identity, 10–15 reference boluses in manifest, constraints. Highest signal-per-token ratio. |
| Soft maximum | 4,000 | Configurable via `circle1_max_tokens`. Beyond this, the injection consumes meaningful context budget. The assembler warns but does not truncate. |
| Hard ceiling | 6,000 | The assembler refuses to generate. If above 6K, too much content is inline — demote detail to reference boluses, tighten summaries. |

---

## Reference Example

A complete, well-formed `anamnesis.md` for a coding session:

```markdown
<knowledge>
Physician-builder. Solo operator. Primary stack: Python and TypeScript.
Building AI agent infrastructure (Anamnesis, Atlas) and a career intelligence
platform (Cortivus). Mac Mini M4 Pro as primary development machine.

Working on Anamnesis framework Phase 1 — completed S01-S03, S04 next.

Prefer terse, direct communication. No trailing summaries.
Do not hallucinate credentials or certifications. If uncertain, ask.
Qualify unconfirmed facts with provenance: "Based on a prior conversation..."

## Available Knowledge
- **Anamnesis Project**: Knowledge framework for LLM agents, Phase 1 in progress. -> `anamnesis-project`
- **Credentials**: MD, MPH, Google Cloud certificate. -> `credentials`
- **Infrastructure**: Mac Mini M4 Pro, macdevserver (Ubuntu), home network topology. -> `infrastructure`
- **Python Patterns**: FastAPI, uv, pytest conventions. -> `python-patterns`
- **Technical Skills**: Python, TypeScript, LangGraph, FastAPI, SQLite, Next.js. -> `technical-skills`
</knowledge>
```

The same system in philosophy mode (different boluses active):

```markdown
<knowledge>
Physician-builder. Interests in philosophy of mind, phenomenology, and
medical ethics. Currently reading Merleau-Ponty's Phenomenology of Perception.

Engage substantively with philosophical arguments. Don't oversimplify.
Qualify unconfirmed attributions.

## Available Knowledge
- **Credentials**: MD, MPH. -> `credentials`
- **Medical Ethics**: Clinical ethics frameworks, case-based reasoning. -> `medical-ethics`
- **Philosophy Reading**: Current reading list, key arguments, open questions. -> `philosophy-reading`
</knowledge>
```
