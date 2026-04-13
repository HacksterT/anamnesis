# Needed Features — Status Audit

Last updated: 2026-04-12

---

## 1. CLI Tool (Agent Interface) — DONE

Implemented in F01-S06. All commands working: `init`, `serve`, `assemble`, `validate`, `metrics`, `bolus` group (list/show/create/update/delete/activate/deactivate/append), `agent` group (list/show/recency), `curation` group (list/confirm/reject/defer), `compile`.

**Remaining gaps:**
- No `anamnesis curation stage` CLI command (currently must use REST or library directly)
- No `anamnesis bolus edit` command (open in $EDITOR)

---

## 2. Web Dashboard (Human Interface) — DONE (core + Circle 3)

Implemented in F01-S07 (core), updated through F04-S03.

**What's working:**
- Framework landing page with concentric circles diagram
- Circle 1: Injection preview with token budget bar
- Circle 2: Boluses — list, toggle, filter, create form
- Circle 3: Curation queue — confirm/reject/defer, Stage Fact form
- Circle 4: Episode list
- Settings: Agent registry with recency budget slider

**Remaining gaps:**
- Click-to-edit bolus content (markdown editor) — currently view-only
- Sort controls on bolus list (by name, date, priority)
- "Assemble now" button on Circle 1 page
- Circle 5 — placeholder only

---

## 3. Agent Onboarding — DONE

Per-agent bolus profiles, injection routing, and recency isolation all implemented in F03-S01/S02.

**What's working:**
- `GET /v1/knowledge/injection?agent=ezra` returns Ezra-specific injection
- Per-agent `_recency-{name}` boluses — agents don't overwrite each other
- Agent profiles stored in `anamnesis.yaml` under `agents:`

**No remaining gaps** for the core multi-agent use case.

---

## 4. Conversation Capture & Recency Pipeline — DONE

Implemented in F02. SQLite episode storage, CompletionProvider protocol, recency pipeline.

**No remaining gaps.**

---

## 5. Compilation Pipeline (Circle 4 → Circle 3) — DONE

Implemented in F03-S04. `kf.compile()`, `POST /v1/compile`, `anamnesis compile [--agent]`.
Uses `OpenAICompatibleProvider` (Ollama/Gemma 4 locally).

**No remaining gaps.**

---

## 6. Technical Debt — DONE

Completed in F03-S05:
- Domain exceptions (`BolusExistsError`, `BolusNotFoundError`, `CircleNotConfiguredError`)
- `Literal` types on `BudgetResult.status`, `Turn.role`, `KnowledgeConfig.bolus_store`
- Assembler single-scan (bolus counts on `BudgetResult`)
- Dashboard CSS consolidated in `app.css`

---

## 7. Memory Migration Tooling — DEFERRED

Manual curation process preferred over automated migration. Revisit if bulk onboarding becomes necessary.

---

## Summary: What's Next

| Item | Priority | Phase |
|------|----------|-------|
| `anamnesis curation stage` CLI command | Low | Backlog |
| Bolus click-to-edit in dashboard | Medium | Dashboard UX |
| "Assemble now" button on Circle 1 | Low | Dashboard UX |
| Circle 3 → Circle 2 reconciliation (permissiveness slider, auto-promote) | High | Phase 5 per build order |
| Circle 5: Behavioral mining | Low | Phase 6 |
| Vector search | Low | Phase 7 (only if needed) |
