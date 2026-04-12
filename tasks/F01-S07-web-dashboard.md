---
id: F01-S07
feature: F01
title: Web Dashboard (Human Interface)
priority: Should-Have
status: backlog
created: 2026-04-12
type: software
---

# F01-S07: Web Dashboard (Human Interface)

**Feature:** F01 — Circle 1 & Circle 2 Core
**Priority:** Should-Have

## Summary

Build a web dashboard for human knowledge management. The dashboard provides a visual interface for browsing the bolus library, previewing the assembled injection, managing agent registrations, and (in future phases) reviewing the curation queue. Served from the same FastAPI process as the API, mounted at `/dashboard`.

## Acceptance Criteria

- [ ] Dashboard is accessible at `http://localhost:8741/dashboard` when `anamnesis serve` is running
- [ ] **Bolus Library view:** table/card view of all boluses with title, summary, tags, active status, last updated; toggle activation; click to view/edit; create new; filter by tag/status
- [ ] **Injection Preview view:** rendered `anamnesis.md` with token count, budget bar (green/yellow/red), per-section breakdown, "Assemble now" button
- [ ] **Agent Registry view:** list of onboarded agents, per-agent config summary, link to agent-specific injection preview
- [ ] Dashboard reads/writes through the `/v1/` API endpoints (no direct library calls from the frontend)
- [ ] No separate frontend build step required for development
- [ ] Responsive layout (usable on tablet for review sessions)

## Tasks

### Backend

- [ ] Choose frontend approach: HTMX + Jinja2 templates (no build step, server-rendered) vs lightweight SPA (requires build step). Recommend HTMX for simplicity.
- [ ] Add dashboard dependencies to optional group (`[project.optional-dependencies] dashboard = ["jinja2>=3.1"]`)
- [ ] Mount dashboard routes on FastAPI app at `/dashboard`
- [ ] Implement Bolus Library page — list, filter, toggle, create, edit
- [ ] Implement Injection Preview page — rendered markdown, token budget visualization
- [ ] Implement Agent Registry page — list agents, show config, onboarding form
- [ ] Serve static assets (CSS, minimal JS for HTMX) from package

### Testing & Verification

- [ ] Write tests: dashboard pages render, bolus CRUD via dashboard triggers correct API calls, injection preview shows current state
- [ ] Local Testing: `pytest tests/` passes, dashboard is functional in browser
- [ ] Manual Testing: CHECKPOINT — Verify dashboard UX, bolus management flow, injection preview accuracy

### Git

- [ ] Commit, fetch/rebase, push

## Technical Notes

- HTMX is the recommended approach. It keeps the stack Python-only (Jinja2 templates, no Node/npm), requires no build step, and handles the interactivity needed (toggle switches, inline editing, live preview). If the dashboard needs richer interactivity later, it can be incrementally replaced with a SPA.
- The dashboard is a thin presentation layer over the API. Every action goes through `/v1/` endpoints. This means the dashboard and CLI are always consistent — they share the same data path.
- Future phases add views: Curation Queue (Circle 3 reconciliation), Episode Viewer (Circle 4), Metrics Dashboard. These are additive — new pages, same architecture.

## Blockers

- F01-S06 (CLI & Agent Onboarding) — depends on the agent registry and config file model.
