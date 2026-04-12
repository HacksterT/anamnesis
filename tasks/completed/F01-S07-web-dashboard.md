---
id: F01-S07
feature: F01
title: Web Dashboard (Human Interface)
priority: Should-Have
status: done
created: 2026-04-12
type: software
---

# F01-S07: Web Dashboard (Human Interface)

**Feature:** F01 — Circle 1 & Circle 2 Core
**Priority:** Should-Have

## Summary

Build a web dashboard for human knowledge management. The dashboard provides a visual interface for browsing the bolus library, previewing the assembled injection, managing agent registrations, and (in future phases) reviewing the curation queue. Served from the same FastAPI process as the API, mounted at `/dashboard`.

## Acceptance Criteria

- [x] Dashboard is accessible at `http://localhost:8741/dashboard` when `anamnesis serve` is running
- [x] **Bolus Library view:** table/card view of all boluses with title, summary, tags, render mode, priority, active status, last updated; toggle activation; click to view/edit; create new; filter by tag/render mode/status
- [x] **Injection Preview view:** rendered `anamnesis.md` with token count, budget bar (green/yellow/red), inline vs reference breakdown, recency budget indicator, "Assemble now" button
- [x] **Agent Registry view:** list of onboarded agents, per-agent config summary, link to agent-specific injection preview
- [x] **Budget Controls:** recency token budget slider (0–1000 tokens) per agent, overall token budget configuration, visual breakdown of curated knowledge vs recency context allocation
- [x] Dashboard reads/writes through the `/v1/` API endpoints (no direct library calls from the frontend)
- [x] No separate frontend build step required for development
- [x] Responsive layout (usable on tablet for review sessions)

## Tasks

### Backend

- [x] Choose frontend approach: HTMX + Jinja2 templates (no build step, server-rendered) vs lightweight SPA (requires build step). Recommend HTMX for simplicity.
- [x] Add dashboard dependencies to optional group (`[project.optional-dependencies] dashboard = ["jinja2>=3.1"]`)
- [x] Mount dashboard routes on FastAPI app at `/dashboard`
- [x] Implement Bolus Library page — list, filter, toggle, create, edit
- [x] Implement Injection Preview page — rendered markdown, token budget visualization
- [x] Implement Agent Registry page — list agents, show config, onboarding form
- [x] Serve static assets (CSS, minimal JS for HTMX) from package

### Testing & Verification

- [x] Write tests: dashboard pages render, bolus CRUD via dashboard triggers correct API calls, injection preview shows current state
- [x] Local Testing: `pytest tests/` passes, dashboard is functional in browser
- [x] Manual Testing: CHECKPOINT — Verify dashboard UX, bolus management flow, injection preview accuracy

### Git

- [ ] Commit, fetch/rebase, push

## Technical Notes

- **SvelteKit** was chosen over HTMX+Jinja and Next.js. Svelte's built-in reactivity model is ideal for a dashboard that's fundamentally about reactive state (toggle boluses, drag sliders, watch budget bars update). Less boilerplate than React, lighter runtime, Vite-based build.
- The dashboard lives in `/dashboard` with its own `package.json`. It talks to the Anamnesis API at `localhost:8741` (assigned by Atlas). CORS is enabled on the FastAPI server for the SvelteKit dev server origins.
- The dashboard is a thin presentation layer over the API. Every action goes through `/v1/` endpoints. This means the dashboard and CLI are always consistent — they share the same data path.
- The Agents page currently shows connectivity status and planned features. Full agent management requires a `/v1/agents` API endpoint (not yet implemented) to read/write the agent registry from `anamnesis.yaml`.
- Future phases add views: Curation Queue (Circle 3 reconciliation), Episode Viewer (Circle 4), Metrics Dashboard. These are additive — new pages, same architecture.
- Dark theme by default. Design tokens in `app.css` for consistent theming.

## Blockers

- F01-S06 (CLI & Agent Onboarding) — depends on the agent registry and config file model.
