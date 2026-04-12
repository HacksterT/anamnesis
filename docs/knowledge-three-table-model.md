# Knowledge Architecture: The Three-Table Model

A distilled decision framework for agent knowledge systems. This document replaces the single-table approach with three interlocking tables that separate concerns: what kind of knowledge you have, what engineering approach it needs, and what operational features to layer on.

Like a patient workup, these tables are read together but address different diagnostic questions. Table 1 tells you the nature of the condition. Table 2 tells you the treatment protocol. Table 3 tells you the monitoring and safety plan.

---

## Table 1: Knowledge Kind

**Diagnostic question: "What is this knowledge, and how does it behave when the world changes?"**

This table is about update semantics and natural query patterns — the intrinsic properties of the knowledge itself, independent of how much of it you have or how you store it. Every piece of knowledge in the system is one of these three kinds.

| Kind | What it answers | Update semantic | Natural query pattern | Examples |
|------|----------------|-----------------|----------------------|----------|
| **Declarative** | "What is true?" | **Overwrite.** New version supersedes old. Previous versions are either discarded or archived for audit, but operationally irrelevant. | **Categorical.** The consumer knows what they're looking for, or can describe it in domain terms. "What's our service area?" "Does this customer have a preference?" | Business policies, service boundaries, pricing, customer preferences, FAQ answers, user settings, project architecture decisions, agent capability registries |
| **Episodic** | "What happened?" | **Accumulate.** New entries add to the record. Old entries remain valid — they're history, not stale data. Summaries may compress old entries but don't invalidate them. | **Temporal.** The consumer is anchored in time. "What was I working on last month?" "What happened on that call?" "When did we last discuss X?" Secondarily associative — "that thing we talked about regarding deployments." | Conversation summaries, journal entries, call transcripts, interaction logs, session histories, project activity records, pipeline run logs |
| **Procedural** | "What works?" | **Refine.** The procedure improves with experience. New versions incorporate lessons learned but don't discard the core pattern. May also be static if the procedure is authored once and executed deterministically. | **Pattern-match.** The consumer has a situation and needs to find the matching procedure. "I need to schedule an appointment" → triggers the scheduling skill. "Deploy to production" → triggers the deployment runbook. | Skills, runbooks, workflow templates, call-handling scripts, deployment procedures, escalation protocols |

**How to use this table:** Classify each body of knowledge by kind. This tells you:
- Whether to overwrite, accumulate, or refine when new information arrives (ingestion behavior)
- What kind of index or access pattern to optimize for (retrieval design)
- Whether the consumer needs "the latest," "the history," or "the matching procedure" (injection shaping)

**A note on boundaries:** Some knowledge artifacts contain multiple kinds. A project satellite DB might hold declarative facts (architecture decisions) and episodic entries (what was tried and failed). A wiki page is declarative (current truth), but it was compiled from episodic source material (transcripts). The kind applies to the knowledge *as stored and retrieved*, not to its origin. A compiled FAQ answer is declarative even though it was derived from episodic call data.

---

## Table 2: Volume × Dynamism Matrix

**Diagnostic question: "How much knowledge is there, and how often does it change?"**

This is the engineering strategy selector. Volume and dynamism are the two variables with the most mechanical impact on implementation — they determine whether you need infrastructure (storage backends, search indexes, embedding pipelines, compilation jobs) or whether simple file I/O suffices.

The matrix prescribes the approach for each of the three decision paths: ingestion, retrieval, and injection.

### Volume thresholds

| Volume | Threshold | Intuition |
|--------|-----------|-----------|
| **Small** | < ~5,000 tokens | Fits in a single system prompt injection alongside other context. A plumber's FAQ, a user's preferences, a 3-skill agent's procedures. |
| **Medium** | ~5,000–50,000 tokens | Exceeds a single injection but fits in a context window with selection. A department's policy manual, a project's full documentation, a customer's complete interaction history. |
| **Large** | > ~50,000 tokens | Requires retrieval infrastructure. A hospital's policy corpus, a law firm's case database, a year of call transcripts across 30 tenants. |

### The matrix

|  | **Static** | **Interaction-dynamic** | **Session-dynamic** | **Event-driven** |
|--|-----------|------------------------|--------------------|--------------------|
| | *Changes on human timescales* | *Evolves across conversations* | *Changes within a single session* | *Changes on external triggers* |
| **Small** | **The Simplest Case.** Ingest once, store verbatim (markdown, YAML, SQLite row). No pipeline needed. Retrieve by deterministic path/key lookup. Inject wholesale into system prompt. Pre-compute and cache freely. *Example: static bolus, ATLAS_CLAW.md, agent skill definitions, tenant manifest.* | **The Wiki Pattern.** Ingest via scheduled or threshold-triggered compilation (LLM batch job). Store as structured files (markdown with frontmatter). Retrieve by deterministic file-path lookup. Inject wholesale at session start. *Example: learned knowledge wiki, extracted user preferences, FAQ pages that self-curate from interactions.* | **The Working Memory.** Lives in the active context window — no separate storage needed. Managed by conversation history and compaction. Ingestion is implicit (the conversation itself). Retrieval is immediate (it's already in context). Injection is the context window. Compaction/pruning to keep it lean. *Example: active conversation in Tier 1 conversation_events, in-progress pipeline state.* | **The Notification Pattern.** Ingest on event (webhook, API poll). Store latest state, overwrite previous. Retrieve by direct lookup. Inject at next session start or mid-session if the channel supports it. *Example: real-time appointment slot availability, inventory status updates.* |
| **Medium** | **The Reference Library.** Ingest once, store structured with categorization. Retrieve by category selection (pick relevant sections, not everything). Inject selectively — always inject high-signal categories, conditionally inject the rest based on context. FTS5 keyword search as fallback when category is unclear. *Example: persona knowledge bases (Tier 1.5), comprehensive project documentation.* | **The Growing Journal.** Ingest via automated pipeline (post-interaction extraction, periodic compaction). Store with timestamps and sector tags. Retrieve by time-range filter + FTS5 keyword search. Inject on-demand — too much for wholesale injection, so activate on explicit queries. Compaction and summarization to manage growth. *Example: Tier 3 episodic journal entries at moderate scale, project activity logs.* | **The Pipeline Buffer.** Accumulated state from multi-step agent workflows within a session. Shape aggressively — summarize intermediate outputs before passing downstream. Don't inject raw upstream output into downstream agents. Discard or archive after session completion, extracting durable knowledge (declarative facts, procedural skills) before disposal. *Example: multi-agent pipeline intermediate state, research-then-plan workflows.* | **The Live Feed.** Ingest continuously from external source. Store latest + recent history. Retrieve latest by direct lookup, history by time-range. Inject latest at session start; refresh mid-session if the channel supports push. Staleness tolerance depends on domain. *Example: CRM data, ticket queue status, shift schedules.* |
| **Large** | **The Corpus.** Ingest with chunking, indexing, and likely embedding. Store in indexed database with structured metadata. Retrieve via layered search: deterministic first (known document category), FTS5 second (keyword match), vector third (semantic). Inject as RAG — selected chunks with source attribution. Token budget management critical. *Example: enterprise policy corpus, regulatory library, product catalog with 10K+ SKUs.* | **The Archive.** Ingest via continuous automated pipeline with transformation. Store with full indexing (FTS5 + vector embeddings). Retrieve via hybrid search (FTS5 + vector, RRF fusion). Time-range filters essential for temporal queries. Inject on-demand with re-ranking to select most relevant fragments. Active compaction and summarization to manage growth rate. *Example: Tier 3 at scale (years of personal agent memory), enterprise interaction logs, cross-tenant analytics corpus.* | **Unlikely in practice.** A single session rarely generates > 50K tokens of state. If it does, the architecture needs aggressive shaping and intermediate summarization. This cell is a warning sign that the workflow should be decomposed. | **The Firehose.** Ingest via streaming pipeline with filtering and aggregation. Store aggregated summaries, not raw events. Retrieve aggregated state by category or time-window. Inject summaries, not raw data. Requires explicit decisions about what to aggregate vs. discard. *Example: high-volume IoT telemetry, real-time market data feeds.* |

**How to use this table:** For each body of knowledge, assess its volume and dynamism. The corresponding cell prescribes the engineering approach — what kind of ingestion pipeline, what retrieval mechanism, and what injection strategy. Note that the same knowledge kind (e.g., declarative) can land in different cells depending on volume and dynamism — a plumber's FAQ (small, interaction-dynamic → wiki pattern) and a hospital's policy corpus (large, static → corpus pattern) are both declarative, but they need completely different engineering.

---

## Table 3: Feature Modifiers

**Diagnostic question: "What operational concerns apply on top of the base strategy?"**

These modifiers don't determine the engineering approach (Table 2 does that). They add behaviors, constraints, or capabilities to whatever approach Table 2 prescribes. Think of them as comorbidities and risk factors — they don't change the primary diagnosis, but they change the care plan.

Each modifier is independent. A given knowledge store might have several modifiers active simultaneously.

### Provenance & Trust

Determines how knowledge enters the trusted store and how conflicts are handled.

| Provenance level | Ingestion behavior | Conflict behavior | Audit behavior |
|-----------------|-------------------|-------------------|----------------|
| **Human-authored** | Ingest as ground truth. No confirmation gate. | Wins conflicts with all other provenance levels. | Change tracking optional (human is the authority). |
| **Interaction-derived** | Ingest as provisional. Flag for human review if consequence is high. Lint against human-authored knowledge for contradictions. | Yields to human-authored. Contradictions surfaced to operator. Both versions preserved until resolved. | Source attribution required (which interaction, when). |
| **Agent-synthesized** | Ingest with synthesis metadata (what sources, what method). Subject to periodic review. | Lowest priority. Never overrides human-authored or confirmed interaction-derived. | Full synthesis trail required (inputs, method, confidence). |
| **System-observed** | Ingest when observation thresholds are met (e.g., pattern appears N times, workflow succeeds with K+ steps). Below threshold: discard. | Treated as interaction-derived once threshold is met. | Observation count and threshold recorded. |

### Latency & Timing

Determines when and how knowledge reaches the model.

| Latency constraint | Injection timing | Retrieval constraint | Implication |
|-------------------|-----------------|---------------------|-------------|
| **Real-time (< 200ms)** | Pre-session only. All knowledge assembled before the consumer connects. | No LLM calls at retrieval time. No vector search unless pre-indexed. Deterministic file/path lookup only. | Voice agents, live interactions. Drives toward the wiki pattern (compile ahead of time, inject wholesale). |
| **Interactive (< 2s)** | Pre-session + on-demand tool calls during session. | FTS5 and lightweight search acceptable. Single vector query feasible. | Chat agents, Telegram bots. Most personal assistant use cases. |
| **Deferred (< 30s)** | Background enrichment. Mid-session context loading acceptable. | Hybrid search (FTS5 + vector + RRF) feasible. LLM-assisted re-ranking feasible. | Research workflows, complex queries, `/recall`-style explicit retrieval. |
| **Batch (minutes+)** | Not real-time injection — this is compilation/preparation. | Full-corpus processing. LLM-driven extraction, summarization, compilation. | Nightly wiki compilation, periodic lint, skill extraction, Tier 3 backfill. |

### Consequence & Safety

Determines review gates, attribution requirements, and fallback behavior.

| Consequence level | Review gates | Attribution | Fallback on uncertainty |
|-------------------|-------------|-------------|------------------------|
| **Low** | None. Auto-inject without review. Self-correction through future interactions is acceptable. | Optional. Nice to have but not required. | Agent proceeds with best available knowledge. Errors are inconvenient, not harmful. |
| **Medium** | Periodic lint. Flag contradictions. Human review of flagged items on a regular cadence (not blocking). | Provenance tracked. Source available on request but not surfaced in every response. | Agent qualifies uncertain knowledge ("based on prior interactions..."). Graceful degradation. |
| **High** | Human-in-the-loop before knowledge enters the trusted store. Blocking review for new knowledge. | Mandatory source attribution in every response that uses the knowledge. Full audit trail for all changes. | Agent explicitly states uncertainty. Refuses to act on unverified knowledge in high-stakes contexts. Escalation path to human. |

### Consumer Scope & Visibility

Determines access boundaries and sharing rules.

| Scope | Visibility rule | Implementation pattern |
|-------|----------------|----------------------|
| **Single agent** | All knowledge visible. No access control needed. | Direct injection. No filtering layer. |
| **Multiple agents, same tenant** | Shared access with optional scoping. Some knowledge visible to all agents (declarative), some scoped to originating agent (episodic). | Sector-based visibility rules at query time. The `sector` or `persona` field controls read access. Write records provenance (which agent created this). |
| **Single user, multiple personas** | Same as above, but personas are facets of one user, not separate entities. Declarative shared, episodic persona-scoped. | Atlas pattern: `persona` column as provenance on write, sector-based visibility on read. |
| **Cross-tenant** | Never in the operational system. Cross-tenant knowledge is an analytics/reporting concern, mined from tenant stores, not shared between agents. | Separate system entirely. Aggregation with anonymization. Not part of the agent knowledge architecture. |

### Growth Rate & Lifecycle

Determines compaction, pruning, and storage management strategies.

| Growth pattern | Lifecycle strategy | Warning signs |
|---------------|-------------------|---------------|
| **Bounded** | Design for steady-state volume. Compaction and pruning are housekeeping, not survival. The knowledge converges. | If you're pruning aggressively to keep volume down, the knowledge may not actually be bounded — reassess. |
| **Linear** | Plan for growth. Storage scales proportionally with usage. Tiered storage (hot/warm/cold) becomes relevant when the hot tier exceeds the small volume threshold. Compaction promotes hot → cold. | Hot tier exceeding injection budget. Retrieval latency increasing. Time to add selective retrieval if not already present. |
| **Compounding** | Active curation required. Without deliberate quality management, signal-to-noise degrades. Consolidation sweeps, duplicate detection, relevance decay. | Skill library growing but skill utilization declining. Knowledge store growing but retrieval precision declining. These indicate curation debt. |

---

## How the Three Tables Work Together

**Step 1 — Table 1:** Classify each body of knowledge by kind. This determines update semantics (overwrite / accumulate / refine) and the natural query pattern (categorical / temporal / pattern-match).

**Step 2 — Table 2:** For each body of knowledge, assess volume and dynamism. The matrix cell prescribes the engineering approach for ingestion, retrieval, and injection. This is where you decide whether you need a pipeline, a search index, embeddings, or just file I/O.

**Step 3 — Table 3:** Layer on feature modifiers based on the operational context. Provenance adds trust levels and conflict handling. Latency constrains injection timing. Consequence adds review gates. Scope adds visibility rules. Growth rate adds lifecycle management.

**The result:** A complete prescription for how a specific body of knowledge should be handled. Two bodies of knowledge that are the same kind (both declarative) may get completely different engineering approaches (one is small/static → verbatim/wholesale, the other is large/dynamic → indexed/RAG) and different feature modifiers (one is human-authored/low-consequence, the other is interaction-derived/high-consequence).

### Worked Example: Atlas Tier 1 Semantic Memories

- **Table 1:** Declarative. Overwrite semantics (new facts supersede old). Categorical query pattern.
- **Table 2:** Small volume, interaction-dynamic → **Wiki Pattern cell.** Ingest via post-interaction LLM extraction. Store as structured records (SQLite rows). Retrieve by FTS5 keyword match + recency. Inject wholesale (~400 tokens of FTS5 matches + recent memories).
- **Table 3:** Interaction-derived provenance → provisional, lint against human-authored CLAUDE.md. Interactive latency → pre-turn assembly acceptable. Low consequence → auto-inject without review. Single user, multiple personas → semantic sector shared across personas. Linear growth → compaction promotes to Tier 3, prunes Tier 1.

### Worked Example: Plumber Tenant FAQ Page

- **Table 1:** Declarative. Overwrite semantics (FAQ answers update as new information emerges). Categorical query pattern.
- **Table 2:** Small volume, interaction-dynamic → **Wiki Pattern cell.** Ingest via nightly LLM compilation from transcripts. Store as structured markdown with frontmatter. Retrieve by deterministic file-path lookup. Inject wholesale into system instruction.
- **Table 3:** Interaction-derived provenance → provisional, with owner-confirmation as trust escalation. Real-time latency → pre-session assembly only, no mid-call retrieval. Medium consequence → periodic lint, flag contradictions with bolus. Single agent consumer → no visibility rules. Bounded growth → stabilizes, no aggressive pruning needed.

### Worked Example: Atlas Tier 3 Episodic Journal Entries

- **Table 1:** Episodic. Accumulate semantics (old entries remain valid history). Temporal query pattern (primarily), associative (secondarily).
- **Table 2:** Growing volume (approaching medium), interaction-dynamic → **Growing Journal cell.** Ingest via compaction pipeline (summarize oldest 10 messages, promote with embedding). Store with timestamp index + FTS5 + vector embeddings. Retrieve by time-range filter + hybrid FTS5/vector search with RRF fusion. Inject on-demand only (`/recall`).
- **Table 3:** System-generated provenance (compaction summaries) → periodic review, audit via build log. Deferred latency → hybrid search acceptable, not on the hot path. Low consequence → no review gate. Single user → persona-scoped (episodic visible only to originating persona). Linear growth → unbounded by design, separate SQLite file to avoid impacting Tier 1 performance.

### Worked Example: Voice Agent Scheduling Skill

- **Table 1:** Procedural. Static refinement (authored once, executed deterministically). Pattern-match query pattern.
- **Table 2:** Small volume, static → **Simplest Case cell.** Ingest once at deployment. Store as skill definition in manifest or referenced file. Retrieve by trigger keyword match. Inject as part of system prompt at session start.
- **Table 3:** Human-authored provenance → ground truth, no confirmation needed. Real-time latency → must be pre-loaded, no mid-call skill retrieval. Low consequence → skill failure degrades to general agent behavior. Single agent consumer → no visibility rules. Bounded growth → new skills added by platform, not by agent.
