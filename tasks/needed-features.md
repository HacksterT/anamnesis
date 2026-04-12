# Needed Features — Beyond Phase 1

Phase 1 (S01–S05) delivers the library core: bolus CRUD, injection assembly, and a REST API. What's missing is the surface layer — how agents interact with the system programmatically, how humans manage it visually, and how new agents get onboarded.

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
- Card or table view of all boluses with title, summary, tags, active status, last updated
- Toggle activation with a switch
- Click to view/edit content in a markdown editor
- Create new bolus via form
- Filter by tag, category, active status
- Sort by name, date, status

### Injection Preview
- Live-rendered view of the assembled `anamnesis.md`
- Token count with budget bar (green/yellow/red)
- Per-section breakdown
- "Assemble now" button

### Agent Registry
- List of onboarded agents with their config summaries
- Per-agent view: which boluses are relevant, token budget, last assembly
- Onboarding wizard (walks through `anamnesis init --agent`)

### Future (Phase 2+)
- Curation queue (Circle 3 → Circle 2 reconciliation)
- Episode viewer (Circle 4 raw episodes)
- Metrics dashboard (confirmation rate, queue depth, staleness)

**Design notes:**
- Served from the same FastAPI process as the API (mounted at `/dashboard`)
- Lightweight frontend — could be HTMX + Jinja templates or a small React/Svelte SPA
- No separate frontend build step if using HTMX approach
- Reads/writes through the same `/v1/` API endpoints

---

## 3. Agent Onboarding

When a new agent joins the Anamnesis system, it needs:

1. **A config entry.** Which knowledge directory does it read from? What's its token budget? Which boluses are relevant? What's its permissiveness level?

2. **A knowledge directory** (optional). Agents can share a knowledge directory (same boluses, same injection) or have isolated directories. Shared is the default — most agents reading from the same knowledge base is the common case. Isolated is for multi-tenant or domain-specific agents.

3. **An injection profile.** Which sections of `anamnesis.md` does this agent get? A coding assistant might get Identity + Knowledge Domains + Capabilities. A voice agent might get Identity + Knowledge Domains + Current Context. The profile controls section inclusion.

4. **Registration.** The agent is added to a registry (`anamnesis.yaml` or a `agents/` directory) so the system knows it exists and can serve its injection via the API (`GET /v1/knowledge/injection?agent=atlas`).

**Onboarding flow:**

```
anamnesis init --agent atlas \
  --knowledge-dir knowledge/ \
  --token-budget 4000 \
  --sections identity,domains,capabilities
```

This creates an agent config entry and (if needed) initializes the knowledge directory. The agent can then call:

```
GET /v1/knowledge/injection?agent=atlas
```

And receive its tailored injection.

**Multi-agent model:**
- Default: all agents share `knowledge/` — one bolus library, one injection template
- Override: per-agent knowledge dirs for isolation
- Hybrid: shared bolus library, per-agent section profiles (most likely pattern)

---

## Story Mapping

| Story | Scope | Depends On |
|-------|-------|------------|
| S06 | CLI tool + agent onboarding (`init`, `agent`, `bolus` commands) | S05 (API layer) |
| S07 | Web dashboard (bolus library, injection preview, agent registry) | S06 (agent model) |

S06 is the natural next step after Phase 1. It makes the system usable without writing Python. S07 builds on S06's agent model and adds the visual layer.
