---
type: prd
status: draft
created: 2026-04-06
author: HacksterT + Atlas
parent: ARD.md
---

# PRD -- Learned Knowledge Wiki

A self-curating knowledge layer that compiles customer interactions into structured, per-tenant wiki pages. Agents that opt into this skill accumulate institutional knowledge over time without manual curation.

## Problem

Voice agents (and chat agents) today are grounded in static knowledge boluses -- documents ingested once at onboarding time. The agent knows what the business told it. It does not know what it has learned.

When Aria handles 200 calls for a plumbing company over three months, valuable knowledge is generated and discarded every session:

- The business owner clarifies that they don't service north of Highway 36
- A customer mentions a rebate program the owner confirms is active
- Friday same-day bookings are consistently declined by the owner
- Mrs. Johnson always asks for Dave

This knowledge lives in transcripts that nobody reads. The next caller gets the same day-one agent. The agent never gets smarter.

## Solution

A new skill subgraph (`learned-knowledge`) that:

1. Compiles interaction transcripts into structured wiki pages per tenant
2. Injects relevant wiki content into the agent's system prompt at session start
3. Grows and self-corrects over time as more interactions occur

The wiki is the agent's institutional memory for a specific business. It is separate from the bolus (static, owner-provided knowledge) and complementary to it.

## Architecture

### Where It Lives in the Stack

```
Layer 1  runtime/skills/learned_knowledge.py     Skill subgraph (compile, query, lint)
         runtime/skills/learned_knowledge/       Wiki compiler logic, templates

Layer 2  data/knowledge/{tenant_id}/wiki/        Per-tenant wiki (markdown files)
           index.md                               Master catalog
           log.md                                  Build log
           concepts/                               Atomic knowledge pages
           faq/                                    Self-curating FAQ entries

Layer 2  data/transcripts/{tenant_id}/           Already exists. Source material.
```

No new graph types. No new infrastructure. The wiki is markdown files in the existing tenant knowledge directory, compiled by a skill that any agent can opt into via manifest.

### Data Flow

```
Call handled by Aria (or any agent)
    |
    v
Transcript saved to data/transcripts/{tenant_id}/     [already happens]
    |
    v
Nightly batch job (cron or scheduled task)
    |
    v
learned-knowledge skill: compile operation
    1. Read new/unprocessed transcripts since last compile
    2. Read existing wiki (index.md + relevant pages)
    3. LLM extracts durable knowledge, updates/creates pages
    4. Update index.md, append to log.md
    5. Record compile state (hashes of processed transcripts)
    |
    v
Wiki pages: data/knowledge/{tenant_id}/wiki/
    |
    v
Next call: pre-session assembly injects wiki content
```

### Pre-Session Wiki Injection

At session start (before the caller connects), the voice server assembles a wiki excerpt and prepends it to the system prompt. This happens in `server.py` during profile construction, not in a separate hook.

**Assembly logic (no LLM call, deterministic):**

```python
def assemble_wiki_context(tenant_id: str, caller_id: str | None) -> str:
    """Build wiki injection for system prompt. Fast, no API calls."""
    wiki_dir = KNOWLEDGE_DIR / tenant_id / "wiki"
    parts = []

    # Always inject: FAQ (highest-signal, most common questions)
    faq_path = wiki_dir / "faq" / "top-questions.md"
    if faq_path.exists():
        parts.append(faq_path.read_text())

    # Always inject: active policies and service boundaries
    for page in ["concepts/service-area.md", "concepts/scheduling-policies.md",
                  "concepts/current-promotions.md"]:
        p = wiki_dir / page
        if p.exists():
            parts.append(p.read_text())

    # If known caller: inject their preference page
    if caller_id:
        pref = wiki_dir / f"concepts/caller-{caller_id}.md"
        if pref.exists():
            parts.append(pref.read_text())

    context = "\n\n---\n\n".join(parts)

    # Hard cap: keep injection under 3,000 tokens (~12,000 chars)
    if len(context) > 12_000:
        context = context[:12_000] + "\n\n...(truncated)"

    return context
```

**Token budget:** Target 2,000-3,000 tokens of wiki injection per session. At per-business scale (a plumber, a dental practice), the total wiki after months of calls will be 5-15 pages. The FAQ and key policies fit within budget. Edge cases handled by the truncation cap.

**Gemini Live API consideration:** Wiki content is injected into the system instruction at WebSocket connection time. No mid-call retrieval needed for the MVP. When Gemini Live supports asynchronous tool calling (expected to match 2.5 capabilities), a `query_learned_knowledge` tool can serve as a fallback for questions outside the injected pages.

### Nightly Compilation

A scheduled job runs the compile operation once per day per active tenant.

**Compiler behavior:**

- Reads all transcripts not yet compiled (tracked by SHA-256 hash in `state.json`, same pattern as Cole's memory-compiler)
- Reads the existing wiki index to understand current knowledge state
- Sends transcripts + existing wiki to the LLM with a structured compile prompt
- LLM decides: which facts are durable, which are one-off, which update existing pages, which warrant new pages
- LLM writes/updates wiki pages directly

**Compile prompt priorities (what to extract):**

1. **Corrections from the business owner** -- the owner says "actually we do/don't do X." This is ground truth.
2. **Repeated questions** -- if three callers this week asked about the rebate, that's FAQ material.
3. **Customer preferences** -- named callers with stated preferences (technician, time, method).
4. **Service boundaries** -- geographic, temporal, capability limits discovered through calls.
5. **Pricing and promotions** -- mentioned in calls, confirmed by owner.

**What NOT to extract:**

- One-off caller small talk
- Information already in the static bolus (avoid duplication)
- Unconfirmed claims from callers (only owner-confirmed facts)

**De-duplication:** The compiler reads existing pages before writing. If a fact already exists, it updates the page (adds source reference, adjusts wording if new info refines it). It does not create duplicate entries. The index.md catalog is the primary de-duplication mechanism -- the LLM reads it first and knows what already exists.

### Wiki Page Structure

**Concept pages** (`wiki/concepts/`):

```markdown
---
title: Service Area
sources:
  - "transcripts/2026-04-01_abc123.json"
  - "transcripts/2026-04-15_def456.json"
created: 2026-04-01
updated: 2026-04-15
---

# Service Area

Serves the greater Johnson City area including Jonesborough,
Gray, and Limestone. Does not service north of Highway 36
(Kingsport, Gate City, Weber City).

## Key Details

- Primary radius: ~20 miles from Johnson City
- Emergency calls accepted up to 30 miles (owner discretion)
- Owner confirmed Highway 36 boundary on 2026-04-15 call

## Related

- [[concepts/scheduling-policies]] -- same-day availability
  varies by distance
```

**FAQ pages** (`wiki/faq/`):

```markdown
---
title: Top Questions
auto_generated: true
updated: 2026-04-15
question_count: 8
---

# Frequently Asked Questions

## Do you offer free estimates?
Yes, for jobs within the primary service area. Mentioned in
12 calls since 2026-03-15.

## What's the water heater rebate?
TVA offers a $300 rebate on qualifying heat pump water heaters.
The company handles the rebate paperwork. Confirmed by owner
2026-04-10. Asked about in 7 calls.

## Do you work on weekends?
Saturday mornings only (8 AM - noon). No Sunday service.
Owner confirmed 2026-04-02.
```

The FAQ page is the highest-value artifact. It self-curates based on actual call frequency. No human writes it. No human maintains it.

### Index File

```markdown
# Learned Knowledge Index

| Page | Summary | Last Updated |
|------|---------|-------------|
| [[concepts/service-area]] | Geographic boundaries, Highway 36 limit | 2026-04-15 |
| [[concepts/scheduling-policies]] | Hours, same-day rules, Friday restrictions | 2026-04-12 |
| [[concepts/current-promotions]] | Water heater rebate program details | 2026-04-10 |
| [[concepts/caller-mrs-johnson]] | Prefers Dave, morning appointments | 2026-04-08 |
| [[faq/top-questions]] | 8 most-asked questions with answers | 2026-04-15 |
```

## Skill Implementation

### Skill Registration

The learned-knowledge skill registers like any other skill. Agents opt in via manifest.

**`runtime/src/runtime/skills/learned_knowledge.py`:**

```python
class LearnedKnowledgeInput(SkillInput):
    """Input for learned-knowledge operations."""
    operation: str          # "compile" | "query" | "lint"
    tenant_id: str
    query: str | None       # For query operation
    force_all: bool         # For compile: reprocess all transcripts


class LearnedKnowledgeOutput(SkillOutput):
    """Output from learned-knowledge."""
    pages_created: int
    pages_updated: int
    result: str | None      # For query operation
    errors: list[str]


class LearnedKnowledgeSkill(BaseSkill):
    name = "learned-knowledge"
    description = (
        "Compile customer interaction transcripts into a structured "
        "knowledge wiki. Use 'compile' to process new transcripts, "
        "'query' to search the wiki, 'lint' to health-check."
    )
    input_schema = LearnedKnowledgeInput
    output_schema = LearnedKnowledgeOutput
```

### Manifest Integration

Any agent can opt into learned knowledge by adding it to the manifest skills list and declaring the wiki knowledge path:

```yaml
knowledge:
  boluses:
    - id: company-info
      path: "{tenant_id}/company-info/bolus.db"
      description: "Static company knowledge from onboarding"
  wiki:
    path: "{tenant_id}/wiki/"
    description: "Self-curating knowledge compiled from customer interactions"
    injection_strategy: pre-session       # pre-session | tool-query | both
    max_injection_tokens: 3000

skills:
  - skill_id: learned-knowledge
    display_name: Learned Knowledge
    description: >
      Compiles customer interaction transcripts into a structured
      knowledge wiki that grows over time.
    service_group: document
    triggers:
      - compile knowledge
      - what have I learned
      - update wiki
    input_schema:
      operation: string
      tenant_id: string
      query: string
    output_schema:
      pages_created: int
      pages_updated: int
      result: string
    auth_required: false
    credential_keys: []
    token_cost_estimate: high
    human_review_recommended: false
```

The `wiki` block in the knowledge section is a new manifest field. The `injection_strategy` controls how wiki content reaches the agent:

| Strategy | Behavior | When to Use |
|----------|----------|-------------|
| `pre-session` | Wiki excerpt injected into system prompt at session start. No mid-call retrieval. | MVP. Voice agents where latency matters. |
| `tool-query` | Wiki not injected. Agent calls `query_learned_knowledge` tool when needed. | Chat agents with long sessions, large wikis. |
| `both` | Small excerpt injected + tool available for deeper queries. | When async tool calling is available in Gemini Live. |

### Compilation Job

A CLI command and optional cron entry:

```bash
# Compile new transcripts for a single tenant
uv run python -m runtime.skills.learned_knowledge --tenant ails --compile

# Compile all active tenants
uv run python -m runtime.skills.learned_knowledge --compile-all

# Lint a tenant's wiki
uv run python -m runtime.skills.learned_knowledge --tenant ails --lint

# Query a tenant's wiki
uv run python -m runtime.skills.learned_knowledge --tenant ails --query "What's our rebate policy?"
```

**Cron (production):**

```
0 22 * * * uv run python -m runtime.skills.learned_knowledge --compile-all
```

Runs at 10 PM daily. Only processes tenants with new transcripts since last compile.

## Cost Model

| Operation | Cost per Tenant | Frequency | Monthly (30 tenants) |
|-----------|----------------|-----------|---------------------|
| Nightly compile | $0.30-0.60 | Daily (if new calls) | $180-360 |
| Lint | $0.10-0.20 | Weekly | $12-24 |
| Wiki injection | $0.00 | Per call (no LLM) | $0.00 |

The compile cost scales with transcript volume and wiki size. A tenant with 5 calls/day costs less than one with 50. Tenants with no calls on a given day are skipped (hash-based change detection).

**Cost control levers:**

- Compile frequency: nightly for active tenants, weekly for quiet ones
- Model selection: use a cheaper model (e.g., Haiku, Flash) for compilation since it's a structured extraction task, not creative generation
- Transcript windowing: only compile the last N days of transcripts if wiki is already rich

## Relationship to Existing Knowledge

```
                    Static Knowledge                     Learned Knowledge
                    (bolus)                              (wiki)
Source:             Business owner provides docs          Customer interactions over time
When created:       Onboarding                           Ongoing, automatic
Maintained by:      Human (re-ingest when docs change)   LLM (nightly compile)
Retrieval:          RAG (hybrid FTS + vector)             System prompt injection
Content:            Policies, services, pricing docs      FAQ, preferences, corrections, patterns
Changes:            Rarely                                Continuously
```

Both layers feed the agent. They don't overlap because they come from different sources. The bolus is "what the business says about itself." The wiki is "what the business's customers reveal through interaction."

When they conflict (bolus says "we service Kingsport" but the wiki records the owner saying "we don't go north of Highway 36"), the wiki should note the discrepancy. The nightly lint operation flags contradictions between wiki pages AND between wiki content and bolus content. Resolution requires human review (escalation channel).

## Implementation Phases

### Phase 1 -- MVP (Build It)

- [ ] `LearnedKnowledgeSkill` class with compile and query operations
- [ ] Compile logic: read transcripts, extract knowledge, write wiki pages
- [ ] Wiki page templates: concepts, FAQ, index, log
- [ ] State tracking: `state.json` with transcript hashes
- [ ] `assemble_wiki_context()` in voice server for pre-session injection
- [ ] CLI interface for manual compile/query/lint
- [ ] Manifest schema extension: `knowledge.wiki` block
- [ ] Register skill, wire into Aria manifest for AILS tenant

### Phase 2 -- Harden

- [ ] Structural lint (broken links, orphans, sparse pages)
- [ ] Cross-layer lint (wiki vs. bolus contradiction detection)
- [ ] Compile cost tracking and reporting per tenant
- [ ] Tenant-level compile frequency configuration (daily vs. weekly)
- [ ] Model selection for compiler (default to cheaper model)

### Phase 3 -- Scale

- [ ] Platform UI: business owner can view/edit wiki pages
- [ ] Owner approval flow: flag uncertain facts for owner confirmation
- [ ] `tool-query` injection strategy for chat agents
- [ ] `both` strategy when Gemini Live async tool calling is available
- [ ] Wiki size monitoring and automatic summarization when approaching token budget

## Differentiator

Most voice agent platforms are stateless. They know what they were told at setup. They don't learn.

An agent with a learned knowledge wiki gets smarter with every call. The business owner never has to update a FAQ or correct a knowledge base manually. The top questions page writes itself from actual customer behavior. Service boundaries refine themselves from real interactions.

When a business owner opens their dashboard and sees "Your agent learned 3 new things this week" with a list of FAQ entries that emerged from real calls, that is a retention mechanism that competitors don't have. The agent becomes more valuable the longer it runs. Switching costs increase naturally because the wiki represents months of accumulated, curated institutional knowledge that would be lost.

This is the compounding loop: more calls produce more knowledge, better knowledge produces better calls, better calls produce more business value, more value produces retention.
