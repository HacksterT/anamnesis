---
id: F01-S06
feature: F01
title: CLI Tool & Agent Onboarding
priority: Must-Have
status: backlog
created: 2026-04-12
type: software
---

# F01-S06: CLI Tool & Agent Onboarding

**Feature:** F01 — Circle 1 & Circle 2 Core
**Priority:** Must-Have

## Summary

Build the CLI interface and agent onboarding system. The CLI is the agent's primary tool for knowledge operations — creating boluses, toggling activation, assembling injections, and managing agent registrations. Agent onboarding formalizes how a new agent is registered with Anamnesis and receives its tailored injection.

## Acceptance Criteria

- [ ] `anamnesis init` initializes a knowledge directory with config file, `anamnesis.md`, and `boluses/`
- [ ] `anamnesis init --agent <name>` registers a new agent with configurable token budget and section profile
- [ ] `anamnesis bolus list` shows active boluses; `--all` includes inactive; `--json` outputs JSON
- [ ] `anamnesis bolus show <id>` prints bolus content to stdout
- [ ] `anamnesis bolus create <id> --title "..." --summary "..."` creates a bolus (content from stdin or `--file`)
- [ ] `anamnesis bolus activate <id>` and `deactivate <id>` toggle activation
- [ ] `anamnesis assemble` writes assembled `anamnesis.md`; `--agent <name>` assembles for a specific agent profile
- [ ] `anamnesis metrics` shows token counts, budget utilization, active bolus count
- [ ] `anamnesis agent list` shows registered agents
- [ ] `anamnesis agent show <name>` shows agent config and knowledge summary
- [ ] All commands support `--json` flag for machine-readable output
- [ ] Exit codes: 0 success, 1 error, 2 validation failure
- [ ] Config file (`anamnesis.yaml`) stores defaults, agent registry, and knowledge paths

## Tasks

### Backend

- [ ] Add `typer` as an optional dependency (`[project.optional-dependencies] cli = ["typer>=0.15"]`)
- [ ] Define config file schema (`anamnesis.yaml`) — knowledge paths, default token budget, agent registry
- [ ] Implement config file discovery (current dir → parent dirs → `~/.config/anamnesis/`)
- [ ] Implement `anamnesis init` — create directory structure, write default config
- [ ] Implement `anamnesis bolus` command group — list, show, create, update, delete, activate, deactivate
- [ ] Implement `anamnesis assemble` and `anamnesis validate` and `anamnesis metrics`
- [ ] Implement agent registry — YAML-based, stores per-agent config (token budget, section profile, knowledge dir override)
- [ ] Implement `anamnesis init --agent` and `anamnesis agent list/show`
- [ ] Implement `--json` output mode across all commands
- [ ] Wire CLI entry point in `pyproject.toml` (`[project.scripts]`)

### Testing & Verification

- [ ] Write tests: init creates correct structure, bolus CRUD via CLI, agent onboarding, config discovery, JSON output mode
- [ ] Local Testing: `pytest tests/` passes, CLI commands work end-to-end
- [ ] Manual Testing: CHECKPOINT — Verify CLI UX, config file format, agent onboarding flow

### Git

- [ ] Commit, fetch/rebase, push

## Technical Notes

- S05 already defines `anamnesis serve`, `anamnesis assemble`, and `anamnesis validate` as CLI commands. S06 expands this into a full CLI with the bolus and agent command groups.
- The config file (`anamnesis.yaml`) is separate from `KnowledgeConfig` (the Python dataclass). The YAML file is the on-disk representation; the dataclass is the in-memory runtime object. The CLI reads YAML → instantiates `KnowledgeConfig`.
- Agent profiles control which sections of `anamnesis.md` an agent receives. Default: all sections. Override per agent.

## Blockers

- F01-S05 (API Layer) — depends on the serve command and API endpoints.
