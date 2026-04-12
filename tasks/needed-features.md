# Needed Features — Beyond Phase 1

Phase 1 (S01–S05) delivers the library core: bolus CRUD, injection assembly (render model), and a REST API. What follows is the surface layer (CLI, dashboard), the agent onboarding model, and the conversation capture pipeline.

---

## 1. CLI Tool (Agent Interface) → S06

The CLI is the agent's primary tool for knowledge operations. When an agent needs to create a bolus, toggle activation, trigger assembly, or inspect the knowledge state, it shells out to the CLI or calls the equivalent API. The CLI is also the operator's quick-access tool for scripting and automation.

**Core commands:**

```
anamnesis init                          # Initialize knowledge directory + config
anamnesis init --agent <name>           # Onboard a new agent (see §3)

anamnesis bolus list [--all]            # List active boluses (--all includes inactive)
anamnesis bolus show <id>               # Print bolus content
anamnesis bolus create <id> [--file]    # Create bolus from stdin or file
anamnesis bolus update <id> [--file]    # Update bolus content
anamnesis bolus delete <id>             # Delete bolus
anamnesis bolus activate <id>           # Toggle active
anamnesis bolus deactivate <id>         # Toggle inactive

anamnesis assemble                      # Assemble anamnesis.md from active boluses
anamnesis validate                      # Validate anamnesis.md against schema
anamnesis metrics                       # Show token counts, budget utilization

anamnesis serve                         # Start the REST API (from S05)

anamnesis agent list                    # List onboarded agents
anamnesis agent show <name>             # Show agent config + knowledge summary
anamnesis agent recency <name> --budget 400   # Set recency token budget for agent
```

**Design notes:**
- Built on `click` or `typer` (added as optional dependency)
- All commands operate against a config file (`anamnesis.yaml` or `pyproject.toml` section)
- JSON output mode (`--json`) for agent consumption
- Exit codes follow convention (0 success, 1 error, 2 validation failure)

---

## 2. Web Dashboard (Human Interface) → S07

The web UI is the human's tool for reviewing and managing knowledge. It makes the knowledge base tangible — you can see what's in it, what's active, what the injection looks like, and manage it without memorizing CLI commands.

**Views:**

### Bolus Library
- Card or table view of all boluses with title, summary, tags, render mode, active status, last updated
- Toggle activation with a switch
- Click to view/edit content in a markdown editor
- Create new bolus via form (with render mode and priority selection)
- Filter by tag, render mode, active status
- Sort by name, date, priority, status

### Injection Preview
- Live-rendered view of the assembled `anamnesis.md`
- Token count with budget bar (green/yellow/red)
- Inline vs reference breakdown
- Recency slot budget indicator (see §4)
- "Assemble now" button

### Agent Registry
- List of onboarded agents with their config summaries
- Per-agent view: which boluses are active, token budget, recency budget, last assembly
- Onboarding wizard (walks through `anamnesis init --agent`)

### Budget Controls
- **Recency token slider** — configurable per agent, sets how many tokens of the Circle 1 budget are reserved for recent conversation context (Circle 4 → Circle 1 pipeline). Adjustable in both the dashboard and the CLI.
- Overall token budget configuration (soft max, hard ceiling)
- Visual breakdown: how much of the budget is curated knowledge vs recency context

### Future (Phase 2+)
- Curation queue (Circle 3 → Circle 2 reconciliation)
- Episode viewer (Circle 4 raw episodes)
- Metrics dashboard (confirmation rate, queue depth, staleness)

**Design notes:**
- Served from the same FastAPI process as the API (mounted at `/dashboard`)
- Lightweight frontend — HTMX + Jinja templates (no separate build step)
- Reads/writes through the same `/v1/` API endpoints

---

## 3. Agent Onboarding

When a new agent joins the Anamnesis system, it needs:

1. **A config entry.** Which knowledge directory does it read from? What's its total token budget? What's its recency budget? Which boluses does it activate?

2. **A knowledge directory** (optional). Agents can share a knowledge directory (same boluses, same injection) or have isolated directories. Shared is the default — most agents reading from the same knowledge base is the common case. Isolated is for domain-specific agents.

3. **A bolus activation profile.** Which boluses are active for this agent? In a shared knowledge directory, not every agent needs every bolus. A coding agent activates technical boluses. A philosophy agent activates different ones. The activation profile is per-agent.

4. **A recency budget.** How many tokens of the injection are reserved for recent conversation context? This is the Circle 4 → Circle 1 pipeline budget. Configurable per agent via a slider (dashboard) or flag (CLI).

5. **Registration.** The agent is added to a registry so the system knows it exists and can serve its injection via the API (`GET /v1/knowledge/injection?agent=atlas`).

**Onboarding flow:**

```
anamnesis init --agent atlas \
  --knowledge-dir knowledge/ \
  --token-budget 4000 \
  --recency-budget 400
```

**Migration path for existing agents:**

Atlas already has memories in its system. The onboarding process for an existing agent:
1. `anamnesis init --agent atlas` — creates the agent config
2. Migrate existing memories into boluses (manual or assisted — each memory becomes a bolus with appropriate render mode, priority, and tags)
3. Activate relevant boluses for the agent
4. Verify with `anamnesis assemble --agent atlas` and review the output

Selah is a cold-start on a local Gemma 4 model. The onboarding process:
1. `anamnesis init --agent selah` — creates the agent config
2. Create boluses from scratch (identity, domain knowledge, constraints)
3. The `retrieve_knowledge` tool must work with Selah's local model framework (not just cloud APIs)

**Multi-agent model:**
- Default: all agents share `knowledge/` — one bolus library, per-agent activation profiles
- Override: per-agent knowledge dirs for isolation
- Hybrid: shared bolus library, per-agent activation + recency budgets (most likely pattern)

---

## 4. Conversation Capture & Recency Pipeline (Circle 4 → Circle 1)

**The problem:** Anamnesis manages curated, durable knowledge. But agents also need recent conversation context — what happened in the last session, what's being worked on right now. Claude Code handles this internally (conversation history, context compression). Custom agents like Atlas and Selah do not.

**The solution:** Circle 4 captures raw conversation episodes. A recency pipeline automatically surfaces the most recent context into Circle 1 as a dedicated inline bolus with a capped token budget.

### Architecture

```
Conversation turns
    │
    ▼
Circle 4 (episode storage)
    │
    ├─→ Recency slot in Circle 1 (automatic, capped, FIFO)
    │     - Rendered as an inline bolus (render: inline, high priority)
    │     - Fixed token budget per agent (configurable via slider)
    │     - Most recent context replaces oldest — no accumulation
    │     - Updated after each session or on-demand
    │
    └─→ Compilation pipeline (Phase 3, slower, curated)
          - Extracts durable facts from episodes
          - Routes to Circle 3 for review
          - Confirmed facts become permanent boluses in Circle 2
```

### Recency Token Budget

The recency slot has its own token budget *within* the overall Circle 1 budget. This is the key constraint that prevents context stuffing.

| Setting | Default | Range | Controlled By |
|---------|---------|-------|---------------|
| `recency_budget` | 400 tokens | 0–1000 tokens | Slider in dashboard, flag in CLI, field in agent config |

Example: if the agent's total Circle 1 budget is 4,000 tokens and the recency budget is 400, then 3,600 tokens are available for curated boluses and 400 for recent context.

Setting `recency_budget: 0` disables the recency pipeline entirely — useful for agents that don't need session continuity or that handle context externally (like Claude Code).

### Capture API

```python
kf.capture_turn(role="user", content="Let's work on the Anamnesis S04 story.")
kf.capture_turn(role="assistant", content="I'll start with the assembler...")

# End of session — updates the recency slot
kf.end_session(summary="Implemented injection assembly. 75 tests passing.")

# Or let the system auto-summarize from captured turns
kf.end_session()  # auto-generates summary from Circle 4 episodes
```

### Design Notes

- The recency bolus is a system-managed inline bolus. It has `render: inline` and a reserved priority (e.g., priority 25 — after identity, before general knowledge). The user doesn't create or edit it directly.
- Auto-summarization of sessions requires an LLM call. For Phase 2, this could be a lightweight call (Haiku/Flash) or a simple heuristic (last N turns truncated to budget). The `CompletionProvider` interface deferred from Phase 1 becomes relevant here.
- Episode retention is configurable (`circle4_retention_days` in config). Recency is ephemeral; episodes are the raw record.

---

## 5. Memory Migration Tooling

For agents with existing memory systems (like Atlas), Anamnesis needs a migration path.

### Atlas Migration

Atlas's current memory lives in `~/.claude/` as auto-memory markdown files. Each file maps roughly to a bolus:

```
anamnesis migrate atlas \
  --source ~/.claude/projects/*/memory/ \
  --target knowledge/boluses/ \
  --dry-run
```

The migration tool:
1. Reads existing memory files
2. Extracts frontmatter (or infers metadata from content)
3. Maps each memory to a bolus with appropriate render mode, priority, and tags
4. Writes bolus files to the target directory
5. Reports what was migrated, what was skipped (duplicates, empties), what needs manual review

### Design Notes

- Migration is a one-time operation, not an ongoing sync
- `--dry-run` previews without writing
- Some memories won't map cleanly — the tool flags these for manual curation
- This could be an S06 subcommand or a standalone script

---

## Story Mapping

| Story | Scope | Depends On |
|-------|-------|------------|
| S06 | CLI tool + agent onboarding + recency budget config | S05 (API layer) |
| S07 | Web dashboard (bolus library, injection preview, agent registry, budget sliders) | S06 (agent model) |
| Phase 2 | Circle 4 episode capture + recency pipeline + compilation | S04 (assembler), S06 (agent model) |

S06 is the natural next step after Phase 1. S07 adds the visual layer. Phase 2 adds conversation intelligence.
