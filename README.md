# Anamnesis

> *ἀνάμνησις* — the act of recollection. In medicine, the patient history gathered before diagnosis. Here, the structured memory an AI agent carries into every conversation.

**Anamnesis is a knowledge management framework for LLM agent systems.** It gives your agents a persistent, curated memory that survives across conversations — and keeps a human in control of what the agent actually knows.

Agents don't need RAG for everything. Most of what they need to know fits in a few thousand tokens: who they are, what the project is, how they should behave, what was decided last week. Anamnesis manages that knowledge — curating it, compressing it, and assembling it into a single file the agent reads on every turn.

---

## How It Works

Anamnesis uses a **five-circle model**. Knowledge flows inward through curation — raw conversation history is compiled into candidate facts, which are reviewed by a human, and the confirmed facts become boluses that are assembled into the agent's injection.

```
┌─────────────────────────────────────────────────────────┐
│  Circle 5 — Behavioral Mining     (raw observations)    │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Circle 4 — Episodes           (conversation log) │  │
│  │  ┌─────────────────────────────────────────────┐  │  │
│  │  │  Circle 3 — Curation Queue  (human review)  │  │  │
│  │  │  ┌───────────────────────────────────────┐  │  │  │
│  │  │  │  Circle 2 — Boluses    (knowledge lib) │  │  │  │
│  │  │  │  ┌─────────────────────────────────┐  │  │  │  │
│  │  │  │  │  Circle 1 — anamnesis.md        │  │  │  │  │
│  │  │  │  │  (agent reads this every turn)  │  │  │  │  │
│  │  │  │  └─────────────────────────────────┘  │  │  │  │
│  │  │  └───────────────────────────────────────┘  │  │  │
│  │  └─────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

| Circle | What | Status |
|--------|------|--------|
| 1 | `anamnesis.md` — the assembled injection file the agent reads | Implemented |
| 2 | Boluses — the curated knowledge library (one markdown file per topic) | Implemented |
| 3 | Curation queue — candidate facts awaiting human review | Implemented |
| 4 | Episodes — raw conversation history in SQLite | Implemented |
| 5 | Behavioral mining — pattern extraction from episodes | Planned |

---

## Key Concepts

**Bolus** — A named piece of knowledge: a markdown file with YAML frontmatter. One bolus per topic. Boluses can be rendered `inline` (full text in every injection) or `reference` (a manifest line with a categorical pointer — the agent fetches the full content on demand). Each bolus has a priority, active/inactive toggle, and tags.

**Injection** — The `anamnesis.md` file assembled from active boluses, injected into the agent's system prompt. Token-budgeted. Assembly runs in priority order; overflow raises an error.

**Episode** — A completed conversation session stored in SQLite. The recency pipeline automatically summarizes recent turns into a system-managed bolus, giving the agent short-term memory across sessions.

**Compilation** — A scheduled pipeline that sends uncompiled episodes to an LLM (locally via Ollama, or any OpenAI-compatible endpoint), extracts durable facts as JSON, and deposits them in Circle 3 for human review.

**Curation** — The human-in-the-loop step. Each candidate fact in Circle 3 is confirmed (appended to a target bolus), rejected (discarded), or deferred (kept for later). Nothing reaches Circle 2 without human review — until you configure the permissiveness slider in a future phase.

---

## Install

```bash
# Base library (no heavy dependencies — just PyYAML)
uv sync

# With REST API and dev tools
uv sync --extra api --extra dev

# Dashboard (SvelteKit)
cd dashboard && npm install
```

Requires **Python 3.11+** and **Node.js 18+** (for the dashboard).

---

## Quick Start

### 1. Initialize

```bash
anamnesis init
```

This creates `knowledge/` (your Circle 2 bolus directory) and `anamnesis.yaml` (your project config). Copy `anamnesis.example.yaml` for a fully annotated reference.

### 2. Create your first bolus

```bash
cat <<'EOF' | anamnesis bolus create assistant-identity \
  --title "Assistant Identity" \
  --summary "Core identity and operating style." \
  --render inline --priority 10
You are a technical assistant specializing in Python and API design.
You communicate directly. When uncertain, ask rather than guess.
EOF
```

Or copy from the examples:
```bash
cp examples/boluses/assistant-identity.md knowledge/boluses/
```

### 3. Assemble and inspect the injection

```bash
anamnesis assemble          # writes knowledge/anamnesis.md
anamnesis metrics           # token count + budget utilization
cat knowledge/anamnesis.md  # the file your agent will read
```

### 4. Start the API and dashboard

```bash
./start.sh
# API:       http://localhost:8741
# Dashboard: http://localhost:5175
# API docs:  http://localhost:8741/docs
```

### 5. Use in your agent

```python
from pathlib import Path
from anamnesis import KnowledgeConfig, KnowledgeFramework

kf = KnowledgeFramework(KnowledgeConfig(
    circle1_path=Path("knowledge/anamnesis.md"),
    circle2_root=Path("knowledge/boluses"),
    circle4_root=Path("."),      # enables episode capture + recency
    recency_budget=400,          # token budget for recent conversation context
))

# Inject into your LLM system prompt
injection = kf.get_injection()

# Capture the conversation
kf.capture_turn("user", "Let's work on the auth service.")
kf.capture_turn("assistant", "I'll start with the JWT validation endpoints.")

# End session — writes episode to SQLite, updates recency bolus
kf.end_session(agent="my-agent")
```

---

## The Compilation Pipeline

The compilation pipeline is how Anamnesis learns. It reads uncompiled episodes, sends them to an LLM, extracts durable facts, and deposits them in Circle 3 for review.

```yaml
# anamnesis.yaml
completion_provider:
  type: openai_compatible
  base_url: http://localhost:11434/v1   # Ollama
  model: llama3.2                       # or any instruction model
  api_key: null
```

```bash
# Run manually
anamnesis compile

# Or trigger via API
curl -X POST http://localhost:8741/v1/compile
```

Then open the dashboard → **Circle 3** to review extracted facts and confirm them into boluses.

**The pipeline is explicit — never automatic.** Compilation costs tokens and should be scheduled deliberately (cron job, post-session hook, or manual).

---

## Multi-Agent Setup

Multiple agents can share one Anamnesis instance, each with its own bolus activation profile and isolated recency context.

```yaml
# anamnesis.yaml
agents:
  engineering-agent:
    token_budget: 4000
    recency_budget: 400
    active_boluses:
      - coding-preferences
      - project-context
  support-agent:
    token_budget: 4000
    recency_budget: 200
    active_boluses:
      - product-docs
      - customer-faq
```

```bash
# Agent-specific injection
curl "http://localhost:8741/v1/knowledge/injection?agent=engineering-agent"

# Per-agent recency (each agent has its own _recency-{name} bolus)
kf.end_session(agent="engineering-agent")
```

---

## CLI Reference

```
anamnesis init [--agent NAME]            Initialize project structure
anamnesis serve [--port PORT]            Start REST API (default: 8741)
anamnesis assemble                       Build anamnesis.md from active boluses
anamnesis validate                       Validate injection against schema
anamnesis metrics [--json]               Token counts + budget utilization
anamnesis compile [--agent NAME]         Run compilation pipeline (Circle 4 → 3)

anamnesis bolus list [--all] [--json]
anamnesis bolus show ID [--json]
anamnesis bolus create ID [opts]         Content from --file or stdin
anamnesis bolus update ID [--file F]
anamnesis bolus append ID [--file F]     Append content to existing bolus
anamnesis bolus delete ID
anamnesis bolus activate ID
anamnesis bolus deactivate ID

anamnesis agent list [--json]
anamnesis agent show NAME
anamnesis agent recency NAME --budget N

anamnesis curation list [--json]
anamnesis curation confirm ID --bolus BOLUS_ID
anamnesis curation reject ID
anamnesis curation defer ID
```

---

## REST API

Full API docs at `http://localhost:8741/docs` when the server is running.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/health` | Health check |
| GET | `/v1/knowledge/injection` | Assembled injection (text/markdown). Accepts `?agent=name` |
| GET | `/v1/knowledge/injection/metrics` | Token counts, budget utilization |
| GET | `/v1/knowledge/boluses` | List bolus metadata |
| GET | `/v1/knowledge/boluses/{id}` | Bolus content + metadata |
| POST | `/v1/knowledge/boluses` | Create bolus |
| PUT | `/v1/knowledge/boluses/{id}` | Upsert bolus (201 on create, 200 on update) |
| POST | `/v1/knowledge/boluses/{id}/append` | Append content to existing bolus |
| DELETE | `/v1/knowledge/boluses/{id}` | Delete bolus |
| PATCH | `/v1/knowledge/boluses/{id}/activate` | Activate |
| PATCH | `/v1/knowledge/boluses/{id}/deactivate` | Deactivate |
| GET | `/v1/knowledge/retrieve/{id}` | Retrieve bolus content (tool endpoint, plain text) |
| POST | `/v1/episodes/turn` | Capture a conversation turn |
| POST | `/v1/episodes/end` | End session, write to SQLite |
| GET | `/v1/episodes` | List episodes. Accepts `?agent=name` |
| GET | `/v1/episodes/{id}` | Get full episode with turns |
| POST | `/v1/compile` | Trigger compilation pipeline. Accepts `?agent=name` |
| GET | `/v1/curation` | List pending curation items |
| POST | `/v1/curation` | Stage a fact manually |
| POST | `/v1/curation/{id}/confirm` | Confirm fact → promote to bolus |
| POST | `/v1/curation/{id}/reject` | Reject fact |
| POST | `/v1/curation/{id}/defer` | Defer fact |
| GET | `/v1/agents` | List agents |
| POST | `/v1/agents` | Register agent |
| PATCH | `/v1/agents/{name}` | Update agent config |
| DELETE | `/v1/agents/{name}` | Remove agent |

---

## The `retrieve_knowledge` Tool

For reference-mode boluses, the agent calls this tool to fetch full bolus content on demand rather than injecting everything upfront. Define it once and the agent will use it automatically.

**Claude / Anthropic SDK:**
```python
{
    "name": "retrieve_knowledge",
    "description": "Retrieve the full content of a knowledge bolus by its ID. Use this when the injection references a bolus you need to read in full.",
    "input_schema": {
        "type": "object",
        "properties": {
            "bolus_id": {
                "type": "string",
                "description": "The bolus ID from the knowledge manifest (e.g. 'coding-preferences')"
            }
        },
        "required": ["bolus_id"]
    }
}
```

**Handler:**
```python
response = requests.get(f"http://localhost:8741/v1/knowledge/retrieve/{bolus_id}")
return response.text
```

---

## Configuration Reference

```yaml
# anamnesis.yaml (see anamnesis.example.yaml for full annotations)

circle1_path: knowledge/anamnesis.md      # assembled injection output
circle2_root: knowledge/boluses           # bolus directory
circle4_root: .                           # SQLite database location
circle1_max_tokens: 4000                  # soft token ceiling
circle4_retention_days: 90               # episode retention (null = forever)
recency_budget: 400                       # tokens for _recency bolus (0 = off)

completion_provider:
  type: openai_compatible
  base_url: http://localhost:11434/v1
  model: llama3.2
  api_key: null

api_key: null                             # REST API auth (null = no auth)

agents:
  my-agent:
    token_budget: 4000
    recency_budget: 400
    active_boluses: []
```

---

## Project Structure

```
anamnesis.example.yaml        # Annotated config template
start.sh                      # Start API + dashboard together

src/anamnesis/
├── config.py                 # KnowledgeConfig dataclass
├── framework.py              # KnowledgeFramework — main entry point
├── exceptions.py             # Domain exceptions
├── cli.py                    # argparse CLI
├── bolus/                    # Circle 2 — bolus CRUD + markdown store
├── inject/                   # Circle 1 — assembler + token budget
├── episode/                  # Circle 4 — SQLite episode storage
├── compile/                  # Compilation pipeline (Circle 4 → 3)
├── curation/                 # Circle 3 — curation queue
├── completion/               # LLM abstraction (CompletionProvider protocol)
├── recency/                  # Recency bolus pipeline
└── api/                      # FastAPI REST API

dashboard/                    # SvelteKit web UI
├── src/lib/api.ts            # TypeScript API client
└── src/routes/
    ├── circle-1/             # Injection preview + token budget bar
    ├── circle-2/             # Bolus library (list, toggle, create)
    ├── circle-3/             # Curation queue (confirm / reject / defer)
    ├── circle-4/             # Episode list
    └── settings/             # Agent registry

examples/
└── boluses/                  # Example bolus files to copy and adapt
    ├── assistant-identity.md
    ├── coding-preferences.md
    └── project-context.md

knowledge/                    # Your project's knowledge base (gitignored)
├── anamnesis.md              # Circle 1 — assembled injection (generated)
└── boluses/                  # Circle 2 — your bolus files (private)

tests/                        # pytest suite — 251 tests
```

---

## Roadmap

| Phase | Feature | Status |
|-------|---------|--------|
| F01 | Circle 1 + 2: bolus system, injection assembly, API, CLI, dashboard | Done |
| F02 | Circle 4: episode capture, recency pipeline, multi-agent API | Done |
| F03 | Compilation pipeline (Circle 4 → 3), per-agent profiles, curation queue | Done |
| F04 | External content intake: upsert/append, Circle 3 dashboard UI | Done |
| F05 | Reconciliation: permissiveness slider, auto-promote, contradiction detection | Planned |
| F06 | Dashboard UX: bolus editor, sort controls, batch curation review | Planned |
| F07 | Circle 5: behavioral mining, pattern extraction, confidence ceiling model | Planned |
| F08 | Vector search (only if categorical + FTS5 proves insufficient) | Deferred |

See [`docs/anamnesis/anamnesis-roadmap.md`](docs/anamnesis/anamnesis-roadmap.md) for a detailed phase-by-phase history and rationale.

---

## Documentation

| Document | What |
|----------|------|
| [`docs/anamnesis/anamnesis-framework.md`](docs/anamnesis/anamnesis-framework.md) | Full theory: five-circle model, triage questions, the three knowledge types, reconciliation model |
| [`docs/anamnesis/anamnesis-construction.md`](docs/anamnesis/anamnesis-construction.md) | Implementation blueprint: package structure, design decisions, build order |
| [`docs/anamnesis/anamnesis-agent-reference.md`](docs/anamnesis/anamnesis-agent-reference.md) | API reference for agents and developers: all endpoints, tool definitions, session lifecycle |
| [`docs/anamnesis/anamnesis-roadmap.md`](docs/anamnesis/anamnesis-roadmap.md) | Phase history, current state, reading order, recommended next steps |

---

## Contributing

Contributions welcome. The codebase is intentionally minimal — no ORM, no heavy dependencies, no magic.

- **Python:** `uv sync --extra dev` then `uv run pytest tests/`
- **Linting:** `uv run ruff check src/`
- **Dashboard:** `cd dashboard && npm install && npm run build`

The design decisions that govern contributions are documented in `docs/anamnesis/anamnesis-framework.md` and `docs/anamnesis/anamnesis-construction.md`. Read them before proposing structural changes.

---

## License

Apache 2.0. See [LICENSE](LICENSE).
