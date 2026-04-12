# Anamnesis -- Construction Plan

Implementation architecture for Anamnesis. This document translates the five-circle model, bolus architecture, compilation pipeline, reconciliation model, and injection strategy into a buildable software package.

---

## Design Principle: Library, Not Application

The framework describes circles, boluses, compilation, reconciliation, and injection. Those are primitives. The specific use case (Atlas, voice agent, Selah) determines how the primitives are configured and composed. The implementation is a Python library that any application imports and configures, not a standalone system that applications integrate with.

---

## Stack

**Language:** Python. One language, not two. The framework is about knowledge management, not UI. Python is where the LLM tooling lives (LangGraph, Agent SDK, embedding models). TypeScript is for frontends and APIs. The knowledge layer is Python.

**Package structure:**

```
knowledge-framework/
├── pyproject.toml
├── src/
│   └── knowledge/
│       ├── circles/          # The four-circle model
│       │   ├── circle1.py    # Injection file manager (read/write/validate token budget)
│       │   ├── circle2.py    # Bolus registry (CRUD, retrieval, bolus manifest)
│       │   ├── circle3.py    # Curation layer (staging, reconciliation queue)
│       │   └── circle4.py    # Episode capture (append, hash tracking, retention)
│       │
│       ├── bolus/            # Knowledge bolus primitives
│       │   ├── base.py       # Bolus interface (create, read, update, validate)
│       │   ├── store.py      # Storage backends (markdown dir, SQLite, pluggable)
│       │   └── manifest.py   # Bolus manifest generation for Circle 1
│       │
│       ├── compile/          # Compilation pipeline (Circle 4 → Circle 3)
│       │   ├── pipeline.py   # Orchestrator (trigger, extract, route, track state)
│       │   ├── extractor.py  # LLM extraction (configurable prompt, few-shot)
│       │   └── prompts/      # Default + per-domain extraction prompt templates
│       │
│       ├── reconcile/        # Circle 3 → Circle 2 movement
│       │   ├── queue.py      # Reconciliation queue (list, confirm, reject, defer)
│       │   ├── slider.py     # Permissiveness configuration
│       │   └── ambient.py    # Ambient reconciliation hooks (mid-conversation surfacing)
│       │
│       ├── inject/           # Circle 1 assembly
│       │   ├── assembler.py  # Build the single injection file from components
│       │   └── budget.py     # Token budget enforcement and overflow detection
│       │
│       ├── retrieve/         # Circle 2 retrieval
│       │   ├── pointer.py    # Categorical pointer resolution (path lookup)
│       │   ├── search.py     # FTS5 / keyword search (when volume justifies)
│       │   └── vector.py     # Optional vector search (when scale demands)
│       │
│       ├── metrics/          # Quality measurement (per framework Section 10.2)
│       │   ├── extraction.py # Confirmation rate, miss rate, contradiction rate
│       │   └── reconcile.py  # Review rate, queue depth, staleness
│       │
│       └── config.py         # Framework configuration
```

---

## Key Design Decisions

### Storage Is Pluggable, Not Prescribed

The framework says Circle 2 boluses are "structured storage." The library defines the interface; the application provides the backend.

- **Default:** A directory of markdown files with frontmatter. Works everywhere, human-readable, git-friendly.
- **Alternative:** SQLite (for FTS5 when volume justifies it).
- **Future:** Whatever the application already uses.

The bolus store interface is simple: `read(bolus_id) -> content`, `write(bolus_id, content)`, `list() -> [bolus_id]`, `search(query) -> [results]`.

### LLM Calls Are Abstracted

The compilation pipeline and intent resolution layer need LLM calls. The library does not import `anthropic` or `openai` directly. It defines a `CompletionProvider` interface: `complete(prompt, system) -> str`. The application passes in whatever LLM client it uses.

- Atlas passes in Claude.
- Selah passes in a local model.
- The-agency passes in Gemini for voice agents, Claude for text agents.

The framework doesn't care which model powers it.

### Configuration Is a Single Dataclass

One config object per application instance:

```python
@dataclass
class KnowledgeConfig:
    # Circle paths
    circle1_path: Path          # The injection file
    circle2_root: Path          # Root directory for boluses
    circle3_path: Path          # Curation queue (JSON or SQLite)
    circle4_root: Path          # Raw episode storage

    # Token budget
    circle1_max_tokens: int = 4000

    # Permissiveness (1-5 scale, per framework Section 9.1.7)
    permissiveness: int = 2

    # Compilation
    extraction_prompt: Path | None = None   # Custom, or use default
    compile_trigger: str = "manual"         # manual | post-session | scheduled | threshold
    compile_threshold: int = 5              # Episodes before auto-compile (threshold mode)

    # Retention
    circle4_retention_days: int | None = None  # None = indefinite

    # LLM
    completion_provider: CompletionProvider | None = None

    # Storage backend
    bolus_store: str = "markdown"  # markdown | sqlite
```

Every use case is a different config:

```python
# Atlas -- personal assistant
atlas_config = KnowledgeConfig(
    circle1_path=Path("CLAUDE.md"),
    circle2_root=Path("knowledge/boluses"),
    circle3_path=Path("knowledge/curation.json"),
    circle4_root=Path("knowledge/episodes"),
    permissiveness=3,
    compile_trigger="post-session",
)

# The-agency -- voice agent tenant
tenant_config = KnowledgeConfig(
    circle1_path=Path(f"data/knowledge/{tenant_id}/injection.md"),
    circle2_root=Path(f"data/knowledge/{tenant_id}/boluses"),
    circle3_path=Path(f"data/knowledge/{tenant_id}/curation.json"),
    circle4_root=Path(f"data/transcripts/{tenant_id}"),
    circle1_max_tokens=3000,
    permissiveness=2,
    compile_trigger="scheduled",
    extraction_prompt=Path(f"data/knowledge/{tenant_id}/extraction_prompt.md"),
    circle4_retention_days=90,
)

# Selah -- theological knowledge base (high-consequence, strict curation)
selah_config = KnowledgeConfig(
    circle1_path=Path("system_prompt.md"),
    circle2_root=Path("knowledge/theology"),
    circle3_path=Path("knowledge/curation.json"),
    circle4_root=Path("knowledge/study_sessions"),
    permissiveness=1,
    compile_trigger="manual",
)
```

---

## API Surface

The application interacts with the library through operations that map directly to the framework's concepts:

```python
from knowledge import KnowledgeFramework

kf = KnowledgeFramework(config)

# ─── Circle 1: Injection ───────────────────────────────────────
injection_text = kf.get_injection()          # Returns full Circle 1 content
                                              # for system prompt insertion

# ─── Circle 2: Retrieval ───────────────────────────────────────
content = kf.retrieve("infrastructure")       # Follow a categorical pointer
results = kf.search("PostgreSQL migration")   # FTS5 search across boluses

# ─── Circle 2: Bolus Management ────────────────────────────────
kf.create_bolus("technical-skills", content)  # Human-initiated, ground truth
kf.update_bolus("infrastructure", content)    # Human-initiated update

# ─── Circle 3: Curation ────────────────────────────────────────
kf.stage(fact="User has GCP certificate",     # Agent deposits in Circle 3
         source="session-2026-04-09",
         suggested_bolus="credentials")

queue = kf.get_reconciliation_queue(limit=10) # Prioritized by consequence
kf.confirm(item_id, bolus="credentials")      # Human confirms → Circle 2
kf.reject(item_id)                            # Human rejects → removed
kf.defer(item_id)                             # Human defers → stays

# ─── Circle 3: Ambient Reconciliation ──────────────────────────
suggestion = kf.get_ambient_suggestion()      # Returns one fact to surface
                                              # during conversation, or None

# ─── Circle 4: Episode Capture ─────────────────────────────────
kf.capture_episode(content, metadata)         # Log raw episode
kf.compile()                                  # Run compilation pipeline
                                              # (C4 → C3 + C1 recency update)

# ─── Circle 4 → Circle 2: Human Curation ───────────────────────
kf.curate_from_episode(episode_id,            # Human reads episode,
                       fact="...",            # promotes directly to C2
                       bolus="service-area")

# ─── Metrics ───────────────────────────────────────────────────
stats = kf.get_metrics()                      # Confirmation rate, queue depth,
                                              # extraction quality signals
```

---

## Use Case Integration Patterns

### Atlas (Personal Assistant)

Imports the library and configures it to use CLAUDE.md as Circle 1, existing knowledge directories as Circle 2, and conversation transcripts as Circle 4. The compilation pipeline replaces or supplements the current auto-memory system. Reconciliation surfaced through Telegram via ambient suggestions during natural conversation.

### The-agency (Multi-Tenant Voice Agents)

Imports the library per tenant. Each tenant gets a `KnowledgeConfig` with tenant-scoped paths. The voice server calls `kf.get_injection()` at session start to build the system instruction. The nightly compilation job calls `kf.compile()` for each active tenant. The platform dashboard calls the reconciliation API for business owner review. The library doesn't know it's multi-tenant -- the application manages tenant isolation by instantiating one `KnowledgeFramework` per tenant.

### Selah (Theological Knowledge Base)

Imports the library with permissiveness 1 and manual compilation. Study session transcripts captured as episodes in Circle 4. The human manually triggers compilation and reviews every extracted fact before it enters the theological knowledge base. The library doesn't know it's a theological application -- it enforces strict curation because the config says to.

### Future Applications

Any application imports the library, writes a config, and has the full four-circle model with compilation, reconciliation, and injection without building any of it from scratch.

---

## What the Library Does NOT Include

**No UI.** The reconciliation interface, dashboard, and metrics display are application concerns. The library provides data and operations. Atlas surfaces reconciliation through Telegram. The-agency surfaces it through Next.js. Selah might use a CLI. The library doesn't care.

**No transport layer.** The library doesn't handle MCP, function calling, or skill execution. Those are application concerns (the-agency's LangGraph runtime, Atlas's tool system). The library manages knowledge. Skills manage execution.

**No cron or scheduling.** The library provides `kf.compile()`. The application decides when to call it -- launchd, cron, post-session hook, manual trigger. Scheduling is infrastructure, not knowledge management.

---

## Circle 5: Behavioral Mining Service

### The Statistical Power Argument

Behavioral observations follow a diminishing returns curve. The first 5 observations that you prefer terse communication are high-value -- they establish the pattern. Observations 6-20 confirm it to actionable confidence. Beyond 20, you're paying for confirmation of what's already confirmed.

A behavioral profile that meaningfully changes agent behavior has 15-30 confirmed patterns. Each pattern needs roughly 15 observations to reach confidence. That's 200-450 total observations across all micro-pipelines. Not thousands. At that scale, a graph database is infrastructure overhead without matching value.

| Observations per Pattern | Value | Infrastructure Needed |
|---|---|---|
| 0-5 | Pattern detected, low confidence | JSON files, manual review |
| 5-20 | Pattern confirmed, actionable | JSON files + index, compilation script |
| 20-50 | Confidence solidified, diminishing returns | Same. No upgrade needed. |
| 50+ | Confirmation of the obvious | Same. Stop collecting for this pattern. |

### JSON + Index Architecture

The knowledge graph is a JSON index file pointing to JSON content files. No graph database. The index is the graph. The files are the content. Script-assisted traversal reads the index and follows pointers.

```
behavioral-mining/
├── index.json                    # The traversal map (nodes + relationships)
├── config.yaml                   # Which pipelines are active, agent routing
├── observations/                 # Circle 5: raw micro-pipeline output
│   ├── os-usage/
│   │   ├── 2026-04-09-001.json
│   │   └── 2026-04-09-002.json
│   └── bible-study/
│       └── 2026-04-09-001.json
├── patterns/                     # Circle 3: compiled candidates
│   ├── keyboard-efficiency.json
│   └── study-frequency.json
└── profiles/                     # Circle 2: confirmed markdown boluses
    ├── atlas-behavioral.md
    └── selah-behavioral.md
```

### The Index File

The index replaces a graph database's traversal engine with a simple lookup structure:

```json
{
  "nodes": {
    "pattern:keyboard-efficiency": {
      "type": "pattern",
      "file": "patterns/keyboard-efficiency.json",
      "agent": "atlas",
      "confidence": 0.82,
      "observation_count": 23,
      "last_updated": "2026-04-09",
      "status": "circle3"
    },
    "pattern:study-frequency": {
      "type": "pattern",
      "file": "patterns/study-frequency.json",
      "agent": "selah",
      "confidence": 0.91,
      "observation_count": 18,
      "last_updated": "2026-04-08",
      "status": "circle2"
    },
    "source:os-usage": {
      "type": "source",
      "directory": "observations/os-usage/",
      "agent": "atlas",
      "observation_count": 47,
      "last_observation": "2026-04-09"
    }
  },
  "relationships": [
    {
      "from": "pattern:keyboard-efficiency",
      "to": "pattern:terminal-tab-completion",
      "type": "co-occurs",
      "weight": 0.7,
      "evidence_count": 15
    },
    {
      "from": "source:os-usage",
      "to": "pattern:keyboard-efficiency",
      "type": "feeds",
      "observation_count": 23
    }
  ]
}
```

Traversal is reading the index and filtering. "What patterns does the os-usage pipeline feed?" is a list comprehension against the relationships array. Multi-hop traversal is sequential reads. At 30 patterns and a few hundred relationships, the index is ~10KB. This is trivial.

### Traversal Mechanisms

The underlying architecture supports multiple traversal approaches. The index is the foundation; the traversal mechanism is a deployment decision:

**Deterministic scripts.** The default. A Python script reads the index, filters by node type or relationship type, follows pointers, reads content files. Handles all compilation and reconciliation workflows. No LLM needed.

**LLM-light compilation.** For pattern detection from raw observations, a lightweight LLM call replaces statistical analysis:

1. Read the last N observation files from a pipeline
2. Read existing patterns from the index
3. Pass both to a cheap model: "Given these observations and existing patterns, are there new patterns worth proposing or existing patterns to update? Return structured JSON."
4. Write new pattern files and update the index

Cost per compilation run: pennies (Haiku/Flash over 20-30 observations). Run weekly or on threshold (N new observations).

**Agent skill traversal.** The main agent can traverse the behavioral graph through a procedural skill (per Section 9.2). A "review behavioral profile" skill reads the index, navigates patterns, and presents findings -- all through the skill's internal tool calls, invisible to the LLM at the agent level. This is the framework's own architecture applied to its own data: the skill orchestrates traversal internally, the agent just invokes "review behavioral profile" as a capability.

The skill approach is particularly useful for reconciliation. The agent can surface Circle 3 candidates during conversation ("I've noticed you tend to navigate manually instead of using keyboard shortcuts -- should I add that to your profile?") by reading the index, finding unreconciled patterns, and presenting the highest-confidence ones. This is ambient reconciliation implemented as a skill.

### Confidence Ceiling

Once a pattern reaches a confidence threshold (configurable, default 0.9 or 20 confirming observations), the compilation pipeline stops counting new observations for that pattern. It only reopens the count if:

- A contradicting observation appears (drift detection)
- The pattern's evidence ages beyond a recency threshold (staleness)
- The human explicitly requests reanalysis

This caps storage growth, caps processing cost, and forces compilation effort toward patterns that are still uncertain. The system self-limits rather than growing without bound.

### When to Graduate to a Graph Database

The JSON + index model serves until:

- **Per-tenant index exceeds ~100KB** (thousands of patterns with complex relationships). Unlikely for behavioral profiles. Possible for enterprise multi-tenant analytics across behavioral data.
- **Real-time traversal is needed mid-conversation** and file I/O latency becomes measurable. The framework's design avoids this (compilation is batch, injection is pre-computed), but a future use case might require it.
- **Complex conditional queries** become common ("patterns that correlate with other patterns only when a third condition is present, weighted by time of day"). At that point, Cypher or SPARQL earn their place.

The JSON documents migrate cleanly into Neo4j nodes and edges because the data model is already graph-shaped -- just stored flat. The graduation path is a storage migration, not an architectural change.

---

## Build Order

Per the validation path in framework Section 10.5, ordered from highest-confidence to lowest-confidence components:

| Phase | Components | What It Validates |
|-------|-----------|-------------------|
| 1 | `inject/` + `bolus/` + `config.py` | Circle 1 and Circle 2. Injection assembly, bolus CRUD, retrieval. Immediate value. |
| 2 | `circles/circle4.py` | Episode capture. Formalize transcript logging as Circle 4. |
| 3 | `compile/` | Compilation pipeline. Circle 4 → Circle 3. The hardest piece. Validate extraction quality on real data. |
| 4 | `reconcile/` | Circle 3 → Circle 2 operations. Build the queue, measure review rates, test ambient surfacing. |
| 5 | `metrics/` | Quality measurement. Confirmation rate, miss rate, contradiction rate. Feeds back into extraction prompt refinement. |
| 6 | `circles/circle5.py` + `mining/` | Behavioral mining service. Micro-pipeline framework, JSON + index architecture, behavioral compilation mode. |
| 7 | `retrieve/vector.py` | Optional vector search. Only when a specific use case exceeds the FTS5 threshold. |

Each phase validates the assumptions the next phase depends on. The framework is built from the center (Circle 1) outward (Circles 4 and 5), which mirrors the trust gradient and ensures the highest-value layers are working before the more speculative layers are added.

---

## Package Structure (Updated for Five Circles)

```
knowledge-framework/
├── pyproject.toml
├── src/
│   └── knowledge/
│       ├── circles/
│       │   ├── circle1.py    # Injection file manager
│       │   ├── circle2.py    # Bolus registry
│       │   ├── circle3.py    # Curation layer
│       │   ├── circle4.py    # Episode capture
│       │   └── circle5.py    # Behavioral mining observations
│       │
│       ├── bolus/            # Knowledge bolus primitives
│       │   ├── base.py
│       │   ├── store.py      # Pluggable storage backends
│       │   └── manifest.py   # Bolus manifest generation for Circle 1
│       │
│       ├── compile/          # Compilation pipeline
│       │   ├── pipeline.py   # Orchestrator (episodic + behavioral modes)
│       │   ├── extractor.py  # LLM extraction (configurable prompt)
│       │   ├── behavioral.py # Behavioral pattern detection (LLM-light)
│       │   └── prompts/      # Default + per-domain extraction templates
│       │
│       ├── mining/           # Circle 5: Behavioral mining service
│       │   ├── index.py      # JSON index manager (nodes, relationships, traversal)
│       │   ├── pipeline.py   # Micro-pipeline framework (config, routing, scheduling)
│       │   ├── confidence.py # Confidence scoring, ceiling, drift detection
│       │   └── pipelines/    # Built-in micro-pipeline templates
│       │       ├── os_usage.py
│       │       └── template.py
│       │
│       ├── reconcile/
│       │   ├── queue.py
│       │   ├── slider.py     # Permissiveness configuration
│       │   └── ambient.py    # Ambient reconciliation hooks
│       │
│       ├── inject/
│       │   ├── assembler.py  # Build single injection file from components
│       │   └── budget.py     # Token budget enforcement
│       │
│       ├── retrieve/
│       │   ├── pointer.py    # Categorical pointer resolution
│       │   ├── search.py     # FTS5 / keyword search
│       │   └── vector.py     # Optional vector search
│       │
│       ├── metrics/
│       │   ├── extraction.py
│       │   └── reconcile.py
│       │
│       └── config.py         # Framework configuration (updated for 5 circles)
```

---

## Reference

- Framework: [anamnesis-framework.md](anamnesis-framework.md)
- Behavioral Analysis: [anamnesis-behavioral-mining.md](anamnesis-behavioral-mining.md)
- Learned Knowledge Wiki PRD: `/Users/hackstert/Projects/the-agency/docs/design/PRD-learned-knowledge-wiki.md`
- The-agency architecture: `/Users/hackstert/Projects/the-agency/docs/design/ARD.md`

- Framework: [anamnesis-framework.md](anamnesis-framework.md)
- Learned Knowledge Wiki PRD: `/Users/hackstert/Projects/the-agency/docs/design/PRD-learned-knowledge-wiki.md`
- The-agency architecture: `/Users/hackstert/Projects/the-agency/docs/design/ARD.md`
