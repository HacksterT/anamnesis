---
id: F03-S01
feature: F03
title: Per-Agent Bolus Activation Profiles
priority: Must-Have
status: done
created: 2026-04-12
type: software
---

# F03-S01: Per-Agent Bolus Activation Profiles

**Feature:** F03 — Agent Profiles, Injection Routing & Compilation Pipeline
**Priority:** Must-Have

## Summary

Add per-agent bolus activation profiles to the agent registry. Each agent can specify which boluses to activate beyond the defaults. This enables Atlas to activate coding boluses while Selah activates theology boluses — from the same shared knowledge library.

## Acceptance Criteria

- [x] Agent config in `anamnesis.yaml` supports an `active_boluses` list (bolus IDs this agent activates)
- [x] `anamnesis init --agent <name> --boluses infra,skills` sets the initial activation profile
- [x] `PATCH /v1/agents/{name}` accepts `active_boluses` field for updating the profile
- [x] `GET /v1/agents/{name}` returns the `active_boluses` list
- [x] Dashboard Settings page shows per-agent bolus activation toggles
- [x] An empty `active_boluses` list means "use default bolus activation" (no override)
- [x] A non-empty list means "activate these boluses AND boluses with `active: true` by default"

## Tasks

### Backend

- [x] Extend agent config schema in `anamnesis.yaml` to include `active_boluses: list[str]`
- [x] Update `register_agent()` in `init.py` to accept `active_boluses` parameter
- [x] Update agent API endpoints (create, update, get) to handle `active_boluses`
- [x] Update `AgentCreate` and `AgentUpdate` Pydantic models to include `active_boluses`
- [x] Add `get_agent_config(name)` method to `KnowledgeFramework` (reads from YAML)
- [x] Update CLI `init --agent` to accept `--boluses` flag (comma-separated IDs)
- [x] Update CLI `agent show` to display activation profile

### Frontend (Dashboard)

- [x] Add bolus activation toggles to the agent card in Settings page
- [x] Fetch available boluses list to populate toggle options
- [x] PATCH agent on toggle change (debounced)

### Testing & Verification

- [x] Write test: agent with active_boluses list persists to config
- [x] Write test: API returns active_boluses in agent config
- [x] Write test: empty list means no override (default behavior)
- [x] Local Testing: `pytest tests/` passes (195 tests)

### Git

- [x] Commit, fetch/rebase, push

## Blockers

- None — builds on existing agent registry from F01-S06 and F02-S04.
