---
id: F01-S06
feature: F01
title: CLI Tool & Agent Onboarding
priority: Must-Have
status: done
created: 2026-04-12
type: software
---

# F01-S06: CLI Tool & Agent Onboarding

**Feature:** F01 — Circle 1 & Circle 2 Core
**Priority:** Must-Have

## Summary

Build the CLI interface and agent onboarding system. The CLI is the agent's primary tool for knowledge operations — creating boluses, toggling activation, assembling injections, and managing agent registrations. Agent onboarding formalizes how a new agent is registered with Anamnesis and receives its tailored injection.

## Acceptance Criteria

- [x] `anamnesis init` initializes a knowledge directory with config file, `anamnesis.md`, and `boluses/`
- [x] `anamnesis init --agent <name>` registers a new agent with configurable token budget, recency budget, and bolus activation profile
- [x] `anamnesis bolus list` shows active boluses; `--all` includes inactive; `--json` outputs JSON
- [x] `anamnesis bolus show <id>` prints bolus content to stdout
- [x] `anamnesis bolus create <id> --title "..." --summary "..."` creates a bolus (content from stdin or `--file`)
- [x] `anamnesis bolus activate <id>` and `deactivate <id>` toggle activation
- [x] `anamnesis assemble` writes assembled `anamnesis.md`; `--agent <name>` assembles for a specific agent profile
- [x] `anamnesis metrics` shows token counts, budget utilization, active bolus count
- [x] `anamnesis agent list` shows registered agents
- [x] `anamnesis agent show <name>` shows agent config and knowledge summary
- [x] `anamnesis agent recency <name> --budget <tokens>` sets the recency token budget for an agent (0–1000, default 400)
- [x] All commands support `--json` flag for machine-readable output
- [x] Exit codes: 0 success, 1 error, 2 validation failure
- [x] Config file (`anamnesis.yaml`) stores defaults, agent registry, and knowledge paths

## Tasks

### Backend

- [x] Add `typer` as an optional dependency (`[project.optional-dependencies] cli = ["typer>=0.15"]`)
- [x] Define config file schema (`anamnesis.yaml`) — knowledge paths, default token budget, agent registry
- [x] Implement config file discovery (current dir → parent dirs → `~/.config/anamnesis/`)
- [x] Implement `anamnesis init` — create directory structure, write default config
- [x] Implement `anamnesis bolus` command group — list, show, create, update, delete, activate, deactivate
- [x] Implement `anamnesis assemble` and `anamnesis validate` and `anamnesis metrics`
- [x] Implement agent registry — YAML-based, stores per-agent config (token budget, section profile, knowledge dir override)
- [x] Implement `anamnesis init --agent` and `anamnesis agent list/show`
- [x] Implement `--json` output mode across all commands
- [x] Wire CLI entry point in `pyproject.toml` (`[project.scripts]`)

### Testing & Verification

- [x] Write tests: init creates correct structure, bolus CRUD via CLI, agent onboarding, config discovery, JSON output mode
- [x] Local Testing: `pytest tests/` passes, CLI commands work end-to-end
- [x] Manual Testing: CHECKPOINT — Verify CLI UX, config file format, agent onboarding flow

### Git

- [ ] Commit, fetch/rebase, push

## Technical Notes

- S05's basic CLI (serve, assemble, validate, metrics) was expanded with `init`, `bolus`, and `agent` command groups using argparse (no typer dependency — keeps it zero-dependency beyond pyyaml).
- The config file (`anamnesis.yaml`) is separate from `KnowledgeConfig` (the Python dataclass). The YAML file is the on-disk representation and also stores the agent registry. The config loader strips non-KnowledgeConfig fields (like `agents`) before instantiating the dataclass.
- Agent registry is a dict in `anamnesis.yaml` under the `agents` key. Each agent entry has `token_budget`, `recency_budget`, and optional `knowledge_dir` override.
- The `init` module (`src/anamnesis/init.py`) handles project initialization and agent registration, separate from the CLI for testability and reuse by the dashboard.

## Blockers

- F01-S05 (API Layer) — depends on the serve command and API endpoints.
