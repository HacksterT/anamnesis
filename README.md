# Anamnesis

A knowledge management framework for LLM agent systems. Library-first Python package that manages curated knowledge injection into any LLM via a single markdown file.

*Anamnesis* (ἀνάμνησις) — the act of recollection. In medicine, the patient history gathered before diagnosis. Here, the structured memory an agent carries into every conversation.

## The Five-Circle Model

Anamnesis organizes agent knowledge into five concentric circles — layers of trust and refinement, from the agent's immediate working memory to raw behavioral observations. Knowledge flows inward through curation: raw data enters at the outer circles and is refined, confirmed, and compressed as it moves toward Circle 1.

### Circle 1 — Injection

The single markdown file (`anamnesis.md`) injected into the LLM system prompt. This is what the agent reads on every turn. It contains inline prose (identity, context, constraints) and a manifest of available knowledge with retrieval pointers. Token-budgeted, assembled automatically from active boluses.

**Status:** Implemented. Assembler, token budget enforcement, `retrieve_knowledge` tool contract.

### Circle 2 — Boluses

The confirmed knowledge library. Each bolus is a markdown file with YAML frontmatter — human-curated, git-friendly, toggleable. Boluses cover everything: identity, facts, skills, constraints, behavioral insights, expert personas. The `render` field controls whether a bolus appears inline (full text in injection) or as a reference pointer (summary + retrieval on demand). The `priority` field controls ordering.

**Status:** Implemented. Full CRUD, activation toggles, render modes, tag-based filtering.

### Circle 3 — Curation

The staging area between raw extraction and confirmed knowledge. Facts extracted from episodes (Circle 4) or proposed by agents land here for review. A reconciliation queue with confirm/reject/defer operations. The permissiveness slider controls how much autonomy the system has — from fully manual review to auto-promotion of high-confidence facts.

**Status:** Not yet implemented. Schema designed (SQLite table in `anamnesis.db`). Phase 3 target (compilation pipeline deposits here).

### Circle 4 — Episodes

Raw conversation capture. Every session's turns are stored in SQLite with timestamps, agent attribution, and compilation status. The recency pipeline automatically summarizes the most recent session into a system-managed inline bolus in Circle 1, giving the agent short-term memory. Episode retention is configurable.

**Status:** Implemented. SQLite storage, capture API, recency pipeline, per-agent token budget for recency slot.

### Circle 5 — Behavioral Mining

The outermost circle. Micro-pipelines observe patterns from raw data — OS usage, study habits, communication preferences, tool usage frequency. Observations accumulate until they reach a confidence threshold, at which point they're compiled into Circle 3 candidates for curation. A JSON index tracks patterns, confidence scores, and relationships. Observation pipelines self-limit: once a pattern is confirmed, collection stops for that pattern.

**Status:** Not yet implemented. Architecture designed (JSON index + observation files, confidence ceiling model). Phase 6 target.

## Install

```bash
uv sync                  # base library (pyyaml only)
uv sync --extra dev      # + pytest, ruff, httpx
uv sync --extra api      # + FastAPI, uvicorn
```

Dashboard (SvelteKit):
```bash
cd dashboard && npm install
```

Requires Python 3.11+ and Node.js 18+ (for dashboard).

## Quick Start

### Initialize

```bash
anamnesis init                           # creates knowledge/ dir + anamnesis.yaml
anamnesis init --agent atlas             # also registers an agent
```

### Start the Services

```bash
./start.sh              # starts both API (port 8741) and dashboard (port 5175)
./start.sh api          # API only
./start.sh dash         # dashboard only
```

Or manually:
```bash
anamnesis serve                          # API at http://localhost:8741
cd dashboard && npm run dev              # dashboard at http://localhost:5175
```

### Create Boluses

```bash
# Inline bolus (full text in injection)
echo "Physician-builder. Solo operator. Python and TypeScript." \
  | anamnesis bolus create coding-identity \
    --title "Coding Identity" \
    --summary "Developer orientation." \
    --render inline --priority 10 --tags "identity"

# Reference bolus (manifest line with retrieval pointer)
echo "Mac Mini M4 Pro, 64GB RAM. Ubuntu dev server. Tailscale mesh." \
  | anamnesis bolus create infrastructure \
    --title "Infrastructure" \
    --summary "Hardware and network topology." \
    --tags "technical"
```

### Assemble and View

```bash
anamnesis assemble                       # writes knowledge/anamnesis.md
anamnesis metrics                        # token counts + budget utilization
anamnesis validate                       # check injection against schema
```

### Capture Conversations

```python
from anamnesis import KnowledgeConfig, KnowledgeFramework

config = KnowledgeConfig(
    circle1_path=Path("knowledge/anamnesis.md"),
    circle2_root=Path("knowledge/boluses"),
    circle4_root=Path("knowledge/episodes"),
    recency_budget=400,
)

kf = KnowledgeFramework(config)

# During a conversation
kf.capture_turn("user", "Let's work on the API layer.")
kf.capture_turn("assistant", "I'll start with the endpoints.")

# End session — writes episode to SQLite, updates recency bolus
kf.end_session(agent="atlas")

# Next conversation starts with recency context in the injection
print(kf.get_injection())
```

## CLI Reference

```
anamnesis init [--agent NAME] [--dir DIR]       Initialize project
anamnesis serve [--port PORT]                   Start REST API
anamnesis assemble                              Build anamnesis.md
anamnesis validate                              Validate injection
anamnesis metrics [--json]                      Token counts + utilization

anamnesis bolus list [--all] [--json]           List boluses
anamnesis bolus show ID [--json]                Show bolus content
anamnesis bolus create ID [--file F] [opts]     Create bolus (content from file or stdin)
anamnesis bolus update ID [--file F]            Update bolus content
anamnesis bolus delete ID                       Delete bolus
anamnesis bolus activate ID                     Activate bolus
anamnesis bolus deactivate ID                   Deactivate bolus

anamnesis agent list [--json]                   List registered agents
anamnesis agent show NAME [--json]              Show agent config
anamnesis agent recency NAME --budget N         Set recency token budget
```

## REST API

All endpoints at `http://localhost:8741`. API docs at `/docs`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/health` | Health check |
| GET | `/v1/knowledge/injection` | Assembled anamnesis.md (text/markdown) |
| GET | `/v1/knowledge/injection/metrics` | Token counts, utilization |
| GET | `/v1/knowledge/boluses` | List bolus metadata |
| GET | `/v1/knowledge/boluses/{id}` | Bolus content + metadata |
| POST | `/v1/knowledge/boluses` | Create bolus |
| PUT | `/v1/knowledge/boluses/{id}` | Update bolus |
| DELETE | `/v1/knowledge/boluses/{id}` | Delete bolus |
| PATCH | `/v1/knowledge/boluses/{id}/activate` | Activate |
| PATCH | `/v1/knowledge/boluses/{id}/deactivate` | Deactivate |
| GET | `/v1/knowledge/retrieve/{id}` | Retrieve bolus content (tool endpoint) |
| POST | `/v1/episodes/turn` | Capture conversation turn |
| POST | `/v1/episodes/end` | End session |
| GET | `/v1/episodes` | List episodes |
| GET | `/v1/episodes/{id}` | Get episode with turns |
| GET | `/v1/agents` | List agents |
| GET | `/v1/agents/{name}` | Get agent config |
| POST | `/v1/agents` | Register agent |
| PATCH | `/v1/agents/{name}` | Update agent config |
| DELETE | `/v1/agents/{name}` | Remove agent |

## Project Structure

```
knowledge/
├── anamnesis.md                  # Circle 1 — assembled injection file
└── boluses/                      # Circle 2 — one .md per bolus

src/anamnesis/
├── config.py                     # KnowledgeConfig dataclass
├── framework.py                  # KnowledgeFramework entry point
├── init.py                       # Project init + agent registry
├── cli.py                        # CLI entry points
├── bolus/                        # Circle 2 — bolus CRUD + storage
│   ├── base.py                   # BolusStore ABC
│   ├── store.py                  # MarkdownBolusStore
│   └── frontmatter.py            # YAML frontmatter parser
├── inject/                       # Circle 1 — assembly + budget
│   ├── assembler.py              # Builds anamnesis.md from boluses
│   ├── budget.py                 # Token counting + enforcement
│   └── schema.py                 # Render modes, constants, validation
├── episode/                      # Circle 4 — conversation capture
│   ├── model.py                  # Episode + Turn dataclasses
│   └── store.py                  # SQLite-backed episode storage
├── completion/                   # LLM abstraction
│   ├── provider.py               # CompletionProvider protocol
│   ├── heuristic.py              # No-LLM summarizer
│   ├── summarizer.py             # Episode summarization orchestrator
│   └── prompts.py                # Default prompt templates
├── recency/                      # Circle 4 → Circle 1 pipeline
│   └── pipeline.py               # Recency bolus management
└── api/                          # REST API
    ├── server.py                 # FastAPI app factory
    └── config_loader.py          # YAML config loading

dashboard/                        # SvelteKit web UI (port 5175)
├── src/lib/api.ts                # TypeScript API client
└── src/routes/                   # Pages: boluses, injection, agents
```

## Roadmap

| Phase | Feature | Status |
|-------|---------|--------|
| 1 | Circle 1 + Circle 2 (bolus CRUD, injection assembly, API, CLI, dashboard) | Done |
| 2 | Circle 4 (episode capture, recency pipeline, CompletionProvider, agent API) | Done |
| 3 | Compilation pipeline (Circle 4 → Circle 3, LLM extraction) | Next |
| 4 | Reconciliation (Circle 3 → Circle 2, curation queue, permissiveness slider) | Planned |
| 5 | Metrics (confirmation rate, queue depth, extraction quality) | Planned |
| 6 | Circle 5 (behavioral mining, micro-pipelines, confidence ceiling) | Planned |
| 7 | Vector search (only if categorical + FTS5 proves insufficient) | Planned |

## License

Apache 2.0. See [LICENSE](LICENSE).
