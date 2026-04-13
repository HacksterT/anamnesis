# Needed Features — Status Audit

Last updated: 2026-04-12

---

## 1. CLI Tool (Agent Interface) — DONE

Implemented in F01-S06. All commands working: `init`, `serve`, `assemble`, `validate`, `metrics`, `bolus` group (list/show/create/update/delete/activate/deactivate), `agent` group (list/show/recency). JSON output mode. argparse-based, zero extra dependencies.

**Remaining gaps:**
- `anamnesis bolus create` requires `--file` or stdin — no interactive editor mode
- No `anamnesis bolus edit` command (open in $EDITOR)

---

## 2. Web Dashboard (Human Interface) — DONE (core)

Implemented in F01-S07, restructured with five-circle navigation. SvelteKit + dark theme.

**What's working:**
- Framework landing page with concentric circles diagram and design principles
- Circle 1: Core — injection preview with token budget bar
- Circle 2: Boluses — list, toggle, filter by tag/render mode, create form
- Circle 4: Episodic — episode list from API
- Settings — agent registry with recency budget slider
- Circle 3 and 5 — placeholder pages with feature descriptions

**Remaining gaps:**
- Click-to-edit bolus content (markdown editor) — currently view-only
- Sort controls on bolus list (by name, date, priority)
- "Assemble now" button on Circle 1 page
- Bolus detail/edit page (separate route, not just the list card)
- Dashboard CSS cleanup (some duplicated styles in Circle 1 and Settings pages)

---

## 3. Agent Onboarding — PARTIAL

Basic agent registration works via CLI and API. Agents are stored in `anamnesis.yaml`.

**What's working:**
- `anamnesis init --agent <name>` registers with token/recency budgets
- `GET/POST/PATCH/DELETE /v1/agents` — full CRUD
- Dashboard shows agents with recency slider

**Remaining gaps (significant):**
- **Per-agent bolus activation profiles.** All agents currently see all active boluses. There's no way for Atlas to activate coding boluses while Selah activates theology boluses from the same library. This needs a per-agent activation overlay.
- **Per-agent injection routing.** `GET /v1/knowledge/injection` returns the same injection for all agents. Needs `?agent=atlas` parameter that applies the agent's activation profile and recency budget.
- **Per-agent recency isolation.** Currently one `_recency` bolus shared across all agents. If Atlas and Selah both end sessions, they overwrite each other's recency. Need `_recency-atlas` and `_recency-selah` system boluses.

---

## 4. Conversation Capture & Recency Pipeline — DONE

Implemented in F02. SQLite episode storage, CompletionProvider protocol, heuristic summarizer, recency pipeline with FIFO and budget carve-out.

**No remaining gaps** for the core pipeline. The compilation slow path (Circle 4 → Circle 3) is Phase 3 — a separate feature.

---

## 5. Memory Migration Tooling — DEFERRED

Covered in the Atlas integration PRD as a manual curation process rather than an automated migration tool. The `anamnesis migrate` CLI command is not needed for the initial Atlas onboarding since the human should review each memory before it becomes a bolus.

If automated migration becomes necessary later (e.g., bulk onboarding of many agents with existing memories), it can be scoped then.

---

## 6. Technical Debt & Deferred Improvements — NOT STARTED

All items from the simplify pass are still outstanding:

- **Custom exception types** — `BolusExistsError`, `BolusNotFoundError`, `CircleNotConfiguredError`
- **Literal types** for string discriminators (`status`, `bolus_store`, `role`, `render`)
- **`turn_count` as derived property** on Episode
- **Dashboard CSS cleanup** — complete shared style extraction
- **`BolusUpdate` dead field** — wire `summary` through or remove
- **Assembler double-scan in metrics** — avoid redundant bolus reads

---

## Summary: What Needs a PRD

| Item | Priority | Scope |
|------|----------|-------|
| Per-agent profiles + injection routing | High | Enables Atlas + Selah on shared knowledge base |
| Compilation pipeline (Circle 4 → Circle 3) | High | Phase 3 per build order |
| Technical debt cleanup | Medium | Housekeeping before codebase grows |
| Dashboard enhancements (edit, sort, assemble button) | Medium | UX improvements |
| Dashboard CSS cleanup | Low | Cosmetic |

The per-agent profiles are the critical gap for the personal multi-agent use case (Atlas + Selah sharing one knowledge base). This should be addressed before or alongside the compilation pipeline.
