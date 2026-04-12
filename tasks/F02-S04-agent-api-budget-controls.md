---
id: F02-S04
feature: F02
title: Agent API & Budget Controls
priority: Must-Have
status: done
created: 2026-04-12
type: software
---

# F02-S04: Agent API & Budget Controls

**Feature:** F02 — Circle 4 Episode Capture & Recency Pipeline
**Priority:** Must-Have

## Summary

Expose the agent registry via REST API and wire the recency budget slider in the dashboard. S06 built the agent model and CLI commands; this story makes agents manageable over HTTP and gives the dashboard a functional Agents page with interactive budget controls. After this story, a human can open the dashboard, see their agents, and drag a slider to control how much of each agent's injection budget goes to recency context.

## Acceptance Criteria

- [x] `GET /v1/agents` returns a JSON list of registered agents with their config (token_budget, recency_budget, knowledge_dir)
- [x] `GET /v1/agents/{name}` returns a single agent's config
- [x] `POST /v1/agents` registers a new agent (JSON body: name, token_budget, recency_budget)
- [x] `PATCH /v1/agents/{name}` updates agent config fields (partial update)
- [x] `DELETE /v1/agents/{name}` removes an agent from the registry
- [x] Dashboard Agents page displays registered agents with live data from the API
- [x] Dashboard recency budget slider is functional — dragging it calls `PATCH /v1/agents/{name}` and updates the config
- [x] Dashboard shows token budget allocation visualization: curated vs recency breakdown per agent
- [x] CLI `anamnesis agent recency` command updated to also work via the API (not just direct YAML edit)
- [x] 404 on nonexistent agent for GET/PATCH/DELETE
- [x] 409 on duplicate agent name for POST

## Tasks

### Backend

- [x] Add agent CRUD endpoints to `src/anamnesis/api/server.py`:
  ```
  GET    /v1/agents              -> JSON list of agents
  GET    /v1/agents/{name}       -> JSON agent config
  POST   /v1/agents              -> 201 Created
  PATCH  /v1/agents/{name}       -> 200 OK (partial update)
  DELETE /v1/agents/{name}       -> 200 OK or 404
  ```
- [x] Implement agent API handlers that read/write `anamnesis.yaml` via the `init` module's `load_project_config` / `save_project_config`
- [x] Add Pydantic models: `AgentCreate`, `AgentUpdate`, `AgentResponse`
- [x] Wire the API to discover the config file path (same resolution as CLI: explicit → env → default filenames)

### Frontend (Dashboard)

- [x] Rewrite `dashboard/src/routes/agents/+page.svelte` to fetch from `/v1/agents` and display live data
- [x] Implement agent card component with:
  - Agent name and status
  - Token budget display
  - Recency budget slider (range 0–1000, step 50)
  - Budget allocation bar (visual: curated portion vs recency portion)
  - Save button or auto-save on slider change
- [x] Add agent creation form (name, token_budget, recency_budget)
- [x] Add agent deletion with confirmation
- [x] Add API client functions to `dashboard/src/lib/api.ts`:
  ```typescript
  listAgents(): Promise<Record<string, AgentConfig>>
  getAgent(name: string): Promise<AgentConfig>
  createAgent(name: string, config: AgentConfig): Promise<void>
  updateAgent(name: string, updates: Partial<AgentConfig>): Promise<void>
  deleteAgent(name: string): Promise<void>
  ```

### Testing & Verification

- [x] Write test: agent CRUD lifecycle via REST API (create, read, update, delete)
- [x] Write test: 404 on nonexistent agent
- [x] Write test: 409 on duplicate agent creation
- [x] Write test: PATCH updates only specified fields, preserves others
- [x] Write test: recency_budget update persists to config file
- [x] Write test: agent list returns all registered agents
- [x] Local Testing: `pytest tests/` passes, dashboard builds, slider works in browser
- [x] Manual Testing: CHECKPOINT — Start API + dashboard, register an agent, drag the recency slider, verify config file updates

### Git

- [ ] Commit, fetch/rebase, push

## Technical Notes

- **Config file as the source of truth.** The agent API reads/writes `anamnesis.yaml` directly. No in-memory cache. This means the CLI and API always see the same state. The tradeoff is filesystem I/O on every request, but at the scale of agent management (single-digit agents, infrequent writes), this is negligible.
- **PATCH for partial updates.** The agent update endpoint accepts partial JSON — only the fields present in the request body are updated. Missing fields are preserved. This is cleaner than PUT (which would require the client to send the full agent config).
- **Dashboard auto-save on slider.** The recency slider should debounce and auto-save (PATCH after 500ms of no movement) rather than requiring a separate save button. This feels more responsive for a budget control. The debounce prevents API spam during drag.
- **Budget allocation visualization.** A simple stacked bar: `[====curated====|==recency==]` showing the proportion. Green for curated, blue for recency. Updates in real-time as the slider moves.
- **The slider range (0–1000) is a suggestion, not a hard constraint.** The API should accept any non-negative integer for `recency_budget`. The slider in the dashboard limits to 0–1000 for UX sanity, but a CLI user or API caller can set higher values if they have a specific reason.

## Blockers

- F02-S03 (Recency Pipeline) — depends on `recency_budget` being wired into the assembler and the recency bolus system.
- F01-S06 (CLI & Agent Onboarding) — depends on the agent registry model in `anamnesis.yaml`.
- F01-S07 (Web Dashboard) — depends on the SvelteKit dashboard and API client.
