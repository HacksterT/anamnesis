# Anamnesis Agent Reference

**Audience:** AI agents and agent frameworks connecting to Anamnesis at runtime.  
**Purpose:** Complete technical reference for consuming knowledge injections, calling the REST API, and participating in the knowledge lifecycle as an agent.

---

## 1. What Anamnesis Is

Anamnesis is a knowledge management layer for LLM agents. It maintains a curated library of **knowledge boluses** — discrete, named markdown documents — and assembles them into a single injection file (`anamnesis.md`) that is placed in your context at session start.

You do not search or retrieve from raw sources. You receive a pre-assembled injection at the start of every session, and you call a single tool (`retrieve_knowledge`) to expand any reference pointer into full content on demand.

The system is **library-first**: the same knowledge base can be consumed by multiple agents simultaneously, each receiving a tailored injection based on its registered activation profile.

---

## 2. Core Concepts

### 2.1 Bolus

The atomic unit of knowledge. A bolus is a named markdown document with YAML frontmatter. Each bolus has an `id` (slug, lowercase with hyphens), a `title`, a one-line `summary`, and a `render` mode.

**Render modes:**

| Mode | Behavior in injection |
|------|----------------------|
| `inline` | Full content rendered directly — absorb immediately |
| `reference` | Summary line with retrieval pointer — look up on demand |

Use inline for identity, behavioral rules, and constraints. Use reference for detailed knowledge, project specs, expertise.

### 2.2 Injection (Circle 1)

The assembled `anamnesis.md` is the only thing you read at session start. It contains:

```
<knowledge>
{inline boluses, ordered by priority}

## Available Knowledge
{reference bolus manifest lines, ordered by priority}
</knowledge>
```

The `<knowledge>` wrapper identifies this block as injected knowledge, not conversation or instructions. Everything inside is markdown.

Reference manifest lines follow this format:
```
- **{title}**: {summary} -> `{bolus_id}`
```

The `` -> `{bolus_id}` `` pointer is what you pass to `retrieve_knowledge` to get full content.

### 2.3 Recency (System Bolus)

If the recency pipeline is active, your injection includes a `_recency` (or `_recency-{agent}`) system bolus near priority 25. It summarizes the most recent session turns within the token budget. This is the "where things stand" block. It is automatically managed — do not attempt to create or delete it.

### 2.4 Agent Profile

Each registered agent can have an `active_boluses` list — bolus IDs that are activated specifically for that agent, on top of the library's globally-active boluses. Use the `?agent=` parameter on injection and metrics endpoints to get your tailored view.

---

## 3. How to Connect

### 3.1 API Base URL

The Anamnesis REST API runs at:

```
http://127.0.0.1:8741
```

All endpoints are under `/v1/`. API docs (Swagger UI) are available at `http://127.0.0.1:8741/docs` when the server is running.

### 3.2 Authentication

Authentication is **disabled by default** for local development. If an API key is configured, all requests (except `GET /v1/health`) must include:

```
Authorization: Bearer <api_key>
```

A 401 response with `{"detail":"Invalid or missing API key"}` means authentication is required.

### 3.3 Confirm the Server is Running

```http
GET /v1/health
```

Response:
```json
{"status": "ok", "version": "0.1.0"}
```

---

## 4. REST API Reference

### 4.1 Injection

#### Get Your Injection

The single most important call. Make this at session start.

```http
GET /v1/knowledge/injection
GET /v1/knowledge/injection?agent={agent_name}
```

- Returns `text/markdown` (the fully-assembled `anamnesis.md` content)
- Without `?agent=`: uses default activation profile (all globally-active boluses)
- With `?agent=ezra`: applies Ezra's activation profile and includes only Ezra's recency bolus

Response body: raw markdown, wrapped in `<knowledge>...</knowledge>`.

#### Injection Metrics

```http
GET /v1/knowledge/injection/metrics
GET /v1/knowledge/injection/metrics?agent={agent_name}
```

Response:
```json
{
  "total_tokens": 1240,
  "soft_max": 4000,
  "hard_ceiling": 6000,
  "utilization_pct": 31.0,
  "status": "ok",
  "active_boluses": 7,
  "total_boluses": 12,
  "recency_tokens": 180,
  "recency_budget": 400,
  "agent": "ezra"
}
```

Status values: `"ok"` | `"warning"` (above soft max) | `"error"` (above hard ceiling).

---

### 4.2 Bolus Operations

#### List Boluses

```http
GET /v1/knowledge/boluses
GET /v1/knowledge/boluses?active_only=false
```

Returns array of bolus metadata objects (no content body — summaries only).

```json
[
  {
    "id": "infrastructure",
    "title": "Infrastructure",
    "active": true,
    "render": "reference",
    "priority": 50,
    "summary": "Mac Mini M4 Pro, macdevserver, home network.",
    "tags": ["technical", "hardware"],
    "created": "2026-04-12",
    "updated": "2026-04-12"
  }
]
```

#### Get a Bolus (with content)

```http
GET /v1/knowledge/boluses/{bolus_id}
```

Response:
```json
{
  "id": "infrastructure",
  "metadata": { ... },
  "content": "Full bolus content here..."
}
```

#### Retrieve Knowledge (Tool Endpoint)

**This is the endpoint your `retrieve_knowledge` tool should call.**

```http
GET /v1/knowledge/retrieve/{bolus_id}
```

Returns `text/markdown` — the raw bolus body, no frontmatter, no JSON wrapper. This is what you inject into context as a tool result.

Example: `GET /v1/knowledge/retrieve/infrastructure` returns the full infrastructure document as plain text.

#### Create a Bolus (strict, fails if exists)

```http
POST /v1/knowledge/boluses
Content-Type: application/json

{
  "id": "ai-memory-research",
  "title": "AI Memory Research",
  "summary": "Curated notes on AI memory architectures.",
  "content": "## Overview\n\nContent here...",
  "render": "reference",
  "priority": 50,
  "tags": ["ai", "research"]
}
```

- Returns 201 on success: `{"id": "ai-memory-research", "status": "created"}`
- Returns 409 if the bolus already exists

#### Upsert a Bolus (create or replace)

**Preferred for external agent writes.** Creates the bolus if it doesn't exist; replaces content if it does. On update, existing metadata (title, tags, priority) is preserved — only content and `updated` date change. Metadata fields in the request body are used only on create.

```http
PUT /v1/knowledge/boluses/{bolus_id}
Content-Type: application/json

{
  "content": "Updated content...",
  "title": "AI Memory Research",
  "summary": "Curated notes on AI memory architectures.",
  "render": "reference",
  "priority": 45,
  "tags": ["ai", "research"]
}
```

- Returns 201 `{"id": "...", "status": "created"}` if bolus was new
- Returns 200 `{"id": "...", "status": "updated"}` if bolus existed

#### Append to a Bolus

Adds content to an existing bolus without touching existing content. Useful for accumulating entries (research logs, meeting notes, session insights).

```http
POST /v1/knowledge/boluses/{bolus_id}/append
Content-Type: application/json

{
  "content": "## 2026-04-12 Session Notes\n\nNew findings here...",
  "separator": "\n\n---\n\n"
}
```

- `separator` is optional, defaults to `"\n\n---\n\n"` (renders as horizontal rule in markdown)
- Returns 200 `{"id": "...", "status": "appended"}`
- Returns 404 if bolus does not exist

#### Update a Bolus (content only, existing must exist)

```http
PATCH /v1/knowledge/boluses/{bolus_id}
```

Note: Use `PUT` (upsert) for external agent writes. `PATCH` is available but not the recommended external path.

#### Delete a Bolus

```http
DELETE /v1/knowledge/boluses/{bolus_id}
```

Returns 200 on success, 404 if not found. System boluses (IDs starting with `_`) cannot be deleted.

#### Activate / Deactivate

```http
PATCH /v1/knowledge/boluses/{bolus_id}/activate
PATCH /v1/knowledge/boluses/{bolus_id}/deactivate
```

Returns `{"id": "...", "active": true/false}`.

---

### 4.3 Episode Capture (Circle 4)

If session memory is enabled, capture conversation turns as they happen. The episode is committed to SQLite when `end_session` is called, and the recency bolus is updated automatically.

#### Capture a Turn

```http
POST /v1/episodes/turn
Content-Type: application/json

{
  "role": "user",
  "content": "The message content..."
}
```

Response: `{"status": "captured"}`

Roles: `"user"` | `"assistant"`. Capture both sides of the conversation.

#### End Session

```http
POST /v1/episodes/end
Content-Type: application/json

{
  "summary": "Brief session summary (optional).",
  "agent": "ezra"
}
```

- `agent` matches your registered name so the recency bolus is written to `_recency-{agent}` instead of the shared `_recency`
- Response: `{"status": "ended", "session_id": "2026-04-12T14-30-00-000000Z"}` or `{"status": "no_session", "session_id": null}` if no turns were captured

#### List Episodes

```http
GET /v1/episodes
GET /v1/episodes?agent=ezra
```

Returns array of episode summaries (no turns).

#### Get Episode

```http
GET /v1/episodes/{session_id}
```

Returns full episode with all turns.

---

### 4.4 Agent Registry

#### List Agents

```http
GET /v1/agents
```

Returns object keyed by agent name:
```json
{
  "ezra": {
    "token_budget": 4000,
    "recency_budget": 400,
    "active_boluses": ["coding-patterns", "langraph-notes"]
  }
}
```

#### Get Agent

```http
GET /v1/agents/{name}
```

```json
{
  "name": "ezra",
  "token_budget": 4000,
  "recency_budget": 400,
  "active_boluses": ["coding-patterns"]
}
```

#### Register Agent

```http
POST /v1/agents
Content-Type: application/json

{
  "name": "ezra",
  "token_budget": 4000,
  "recency_budget": 400,
  "active_boluses": ["coding-patterns", "langraph-notes"]
}
```

Returns 201 on success, 409 if name is taken.

#### Update Agent

```http
PATCH /v1/agents/{name}
Content-Type: application/json

{
  "recency_budget": 600,
  "active_boluses": ["coding-patterns", "langraph-notes", "ai-memory-research"]
}
```

All fields are optional. Only supplied fields are updated.

#### Delete Agent

```http
DELETE /v1/agents/{name}
```

---

## 5. The `retrieve_knowledge` Tool

Register this tool with your agent framework. When you see a reference manifest line like:

```
- **Infrastructure**: Mac Mini M4 Pro, macdevserver, home network. -> `infrastructure`
```

Call `retrieve_knowledge("infrastructure")`. Your handler calls `GET /v1/knowledge/retrieve/infrastructure` and returns the markdown response as the tool result.

### Tool Definition (Claude / Anthropic SDK)

```json
{
  "name": "retrieve_knowledge",
  "description": "Retrieve the full content of a knowledge bolus by ID. Use when you need details beyond what the summary in your knowledge prompt provides.",
  "input_schema": {
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

### Tool Definition (OpenAI / function calling)

```json
{
  "type": "function",
  "function": {
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
}
```

### Handler (Python, any framework)

```python
import httpx

def retrieve_knowledge(bolus_id: str) -> str:
    r = httpx.get(f"http://127.0.0.1:8741/v1/knowledge/retrieve/{bolus_id}")
    if r.status_code == 404:
        return f"Bolus '{bolus_id}' not found."
    r.raise_for_status()
    return r.text
```

---

## 6. Session Lifecycle (Standard Pattern)

```
1. Session start
   └── GET /v1/knowledge/injection?agent={name}
       → Inject the returned markdown into your system prompt or as a context message

2. Turn capture (every exchange)
   ├── POST /v1/episodes/turn  {"role": "user", "content": "..."}
   └── POST /v1/episodes/turn  {"role": "assistant", "content": "..."}

3. On-demand retrieval (when needed)
   └── GET /v1/knowledge/retrieve/{bolus_id}
       → Tool result lands in context, available for the rest of the session

4. Session end (when conversation concludes)
   └── POST /v1/episodes/end  {"summary": "...", "agent": "{name}"}
       → Episode saved to SQLite, recency bolus updated for next session
```

---

## 7. Writing Knowledge Back (Intake Pattern)

When you synthesize knowledge worth retaining — curated research, a guide from a transcript, a decision worth remembering — write it back to the bolus system.

**Human-directed write → Circle 2 directly.** If the user explicitly asked you to retain something, upsert it directly to a named bolus. Your judgment acts on the user's authority.

**Agent-autonomous observation → Circle 3 staging (not yet implemented).** If you noticed something that *might* be worth keeping but the user didn't direct you to save it, stage it for human review via `POST /v1/curation` (available after F03-S03).

### Example: Ingest a Research Guide

```python
# Synthesize the guide from raw source
guide_content = synthesize_guide(transcript)

# Write to named bolus — creates on first call, replaces content on subsequent calls
httpx.put(
    "http://127.0.0.1:8741/v1/knowledge/boluses/ai-memory-research",
    json={
        "content": guide_content,
        "title": "AI Memory Research",
        "summary": "Curated notes on AI memory architectures and approaches.",
        "tags": ["ai", "research", "memory"],
        "priority": 50,
    }
)
```

### Example: Accumulate Research Entries

```python
# Append a new entry to the running log — existing content untouched
httpx.post(
    "http://127.0.0.1:8741/v1/knowledge/boluses/ai-memory-research/append",
    json={
        "content": f"## {date.today().isoformat()} — {source_title}\n\n{summary}",
        "separator": "\n\n---\n\n",
    }
)
```

---

## 8. CLI Reference

The `anamnesis` CLI is primarily for human operators. Agents use the REST API. These commands are documented here for completeness and for agents that shell out to the CLI.

```
anamnesis init [--dir KNOWLEDGE_DIR] [--agent NAME] [--token-budget N] [--recency-budget N] [--boluses id1,id2]
anamnesis serve [--config PATH] [--host HOST] [--port PORT]
anamnesis assemble [--config PATH]
anamnesis validate [--config PATH]
anamnesis metrics [--config PATH] [--json]
```

**Bolus commands:**
```
anamnesis bolus list [--all] [--json] [--config PATH]
anamnesis bolus show <id> [--json] [--config PATH]
anamnesis bolus create <id> [--title TEXT] [--summary TEXT] [--render inline|reference]
                           [--priority N] [--tags t1,t2] [--file PATH] [--config PATH]
anamnesis bolus update <id> [--file PATH] [--config PATH]
anamnesis bolus delete <id> [--config PATH]
anamnesis bolus activate <id> [--config PATH]
anamnesis bolus deactivate <id> [--config PATH]
anamnesis bolus append <id> [--file PATH | --content TEXT] [--separator SEP] [--config PATH]
```

**Agent commands:**
```
anamnesis agent list [--json] [--config PATH]
anamnesis agent show <name> [--json] [--config PATH]
anamnesis agent recency <name> --budget N [--config PATH]
```

---

## 9. Python Library Interface

For agents that import Anamnesis directly (e.g., Ezra in the same process):

```python
from anamnesis import KnowledgeConfig, KnowledgeFramework

config = KnowledgeConfig(
    circle1_path="knowledge/anamnesis.md",
    circle2_root="knowledge/boluses",
    circle4_root="knowledge",       # enables episode capture
    recency_budget=400,             # tokens reserved for recency
    circle1_max_tokens=4000,
)
kf = KnowledgeFramework(config)

# ── Injection ──────────────────────────────────────────────────────
injection = kf.get_injection(agent="ezra")        # tailored injection
injection = kf.get_injection()                     # default (no agent filter)
path = kf.assemble(agent="ezra")                   # write to circle1_path

# ── Bolus reads ────────────────────────────────────────────────────
content = kf.read_bolus("infrastructure")          # body only
content = kf.retrieve("infrastructure")            # alias (categorical pointer)
meta = kf.get_bolus_metadata("infrastructure")
boluses = kf.list_boluses(active_only=True, include_system=False)

# ── Bolus writes ───────────────────────────────────────────────────
kf.create_bolus("my-bolus", content, title="...", summary="...", tags=["t"])
kf.update_bolus("my-bolus", new_content)           # must exist
result = kf.upsert_bolus("my-bolus", content)      # create or replace; returns "created" | "updated"
kf.append_bolus("my-bolus", addition, separator="\n\n---\n\n")
kf.set_bolus_active("my-bolus", False)
kf.delete_bolus("my-bolus")                        # system boluses rejected

# ── Episode capture ────────────────────────────────────────────────
kf.capture_turn("user", "The user's message")
kf.capture_turn("assistant", "The assistant's response")
session_id = kf.end_session(summary="Brief summary", agent="ezra")

# ── Episodes ───────────────────────────────────────────────────────
episodes = kf.list_episodes(agent="ezra")
episode = kf.get_episode(session_id)

# ── Metrics ────────────────────────────────────────────────────────
metrics = kf.get_injection_metrics(agent="ezra")
```

---

## 10. Configuration (`anamnesis.yaml`)

The server reads this file from the working directory. The library accepts `KnowledgeConfig` directly.

```yaml
knowledge_dir: knowledge
circle1_max_tokens: 4000
bolus_store: markdown
recency_budget: 400
circle4_retention_days: 90
api_host: "127.0.0.1"
api_port: 8741
# api_key: "your-secret-key"   # uncomment to require auth

agents:
  ezra:
    token_budget: 4000
    recency_budget: 400
    active_boluses:
      - coding-patterns
      - langraph-notes
      - ai-memory-research
```

**Directory layout:**
```
knowledge/
├── anamnesis.md            ← Circle 1: assembled injection (written by assembler)
├── anamnesis.db            ← Circle 4: episode SQLite database
└── boluses/                ← Circle 2: bolus markdown files
    ├── identity.md
    ├── infrastructure.md
    └── ai-memory-research.md
```

---

## 11. Bolus ID Rules

- Lowercase alphanumeric, hyphens only: `[a-z0-9]+(?:-[a-z0-9]+)*`
- Examples: `infrastructure`, `ai-memory-research`, `my-bolus`
- System boluses start with `_` and are managed automatically: `_recency`, `_recency-ezra`
- IDs are slugified on create — `"AI Memory Research"` → `"ai-memory-research"`
- System boluses cannot be deleted via the API or CLI

---

## 12. Error Codes

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 201 | Created |
| 401 | Missing or invalid API key |
| 404 | Resource not found |
| 409 | Conflict (bolus or agent already exists on strict-create) |
| 422 | Validation error (invalid ID, missing required field) |

Error responses have the shape: `{"detail": "Human-readable message"}`.

---

## 13. Agent Onboarding Checklist

1. **Confirm connectivity:** `GET /v1/health` returns `{"status": "ok"}`
2. **Register yourself:** `POST /v1/agents` with your name, token budget, and initial active boluses
3. **Get your injection:** `GET /v1/knowledge/injection?agent={name}` — inject this into your system prompt
4. **Register the `retrieve_knowledge` tool** with your agent framework pointing to `GET /v1/knowledge/retrieve/{bolus_id}`
5. **Wire session capture:** call `POST /v1/episodes/turn` for each exchange; `POST /v1/episodes/end` when done
6. **Write knowledge back:** use `PUT /v1/knowledge/boluses/{id}` (upsert) or `POST /v1/knowledge/boluses/{id}/append` when the user directs you to retain something

---

## 14. Rules for Agents

- **Do not modify system boluses.** Any bolus with an ID starting with `_` is system-managed. Reads are permitted; writes and deletes are blocked.
- **Do not create boluses autonomously.** Upserts and creates should be explicitly directed by the user ("save this," "create a bolus for this topic"). Agent-autonomous observations belong in Circle 3 staging (F04-S02), not Circle 2.
- **Qualify unconfirmed facts.** Knowledge derived from prior conversations or external synthesis should be qualified: "Based on a prior session..." or "I synthesized this from X source — confirm before treating as ground truth."
- **Bolus IDs are stable identifiers.** If you reference a bolus by ID in conversation or in other bolus content, treat the ID as a durable pointer. Do not suggest renaming boluses without user direction.
- **End every session.** Call `POST /v1/episodes/end` with `agent={your_name}` at session close, even if the session was short. This keeps the recency bolus accurate and episode history clean.
- **Use your agent name consistently.** Pass `?agent={name}` to injection and metrics endpoints so you get your tailored view. Pass `"agent": "{name}"` to `end_session` so your recency bolus is isolated from other agents.

---

*Generated: 2026-04-12 — reflects Anamnesis v0.1.0 (F01–F03-S02 complete, F03-S03/S04 and F04-S02 in backlog)*
