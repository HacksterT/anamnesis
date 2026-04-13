---
id: F03-S01
feature: F03
title: Per-Agent Bolus Activation Profiles
priority: Must-Have
status: backlog
created: 2026-04-12
type: software
---

# F03-S01: Per-Agent Bolus Activation Profiles

**Feature:** F03 — Agent Profiles, Injection Routing & Compilation Pipeline
**Priority:** Must-Have

## Summary

Add per-agent bolus activation profiles to the agent registry. Each agent can specify which boluses to activate beyond the defaults. This enables Atlas to activate coding boluses while Selah activates theology boluses — from the same shared knowledge library.

## Acceptance Criteria

- [ ] Agent config in `anamnesis.yaml` supports an `active_boluses` list (bolus IDs this agent activates)
- [ ] `anamnesis init --agent <name> --boluses infra,skills` sets the initial activation profile
- [ ] `PATCH /v1/agents/{name}` accepts `active_boluses` field for updating the profile
- [ ] `GET /v1/agents/{name}` returns the `active_boluses` list
- [ ] Dashboard Settings page shows per-agent bolus activation toggles
- [ ] An empty `active_boluses` list means "use default bolus activation" (no override)
- [ ] A non-empty list means "activate these boluses AND boluses with `active: true` by default"

## Tasks

### Backend

- [ ] Extend agent config schema in `anamnesis.yaml` to include `active_boluses: list[str]`
- [ ] Update `register_agent()` in `init.py` to accept `active_boluses` parameter
- [ ] Update agent API endpoints (create, update, get) to handle `active_boluses`
- [ ] Update `AgentCreate` and `AgentUpdate` Pydantic models to include `active_boluses`
- [ ] Add `get_agent_config(name)` method to `KnowledgeFramework` (reads from YAML)
- [ ] Update CLI `init --agent` to accept `--boluses` flag (comma-separated IDs)
- [ ] Update CLI `agent show` to display activation profile

### Frontend (Dashboard)

- [ ] Add bolus activation toggles to the agent card in Settings page
- [ ] Fetch available boluses list to populate toggle options
- [ ] PATCH agent on toggle change (debounced)

### Testing & Verification

- [ ] Write test: agent with active_boluses list persists to config
- [ ] Write test: API returns active_boluses in agent config
- [ ] Write test: empty list means no override (default behavior)
- [ ] Local Testing: `pytest tests/` passes

### Git

- [ ] Commit, fetch/rebase, push

## Blockers

- None — builds on existing agent registry from F01-S06 and F02-S04.
