# Anamnesis -- Knowledge Strategy Framework

A decision framework for determining how knowledge should be ingested, retrieved, and injected in agent systems. This document treats all information — external data, internal memory, session context, learned procedures — under the generic term **knowledge**, and provides a clinical triage model for selecting the right architectural approach for a given use case.

---

## 1. Foundational Concepts

### 1.1 The Three Decision Paths

Every piece of knowledge in an agent system passes through three independent decision paths. These are related but not identical — the choice made at one path constrains but does not dictate the others.

**Ingestion** — How knowledge enters the system and is transformed for storage. Answers: "What form should this knowledge take at rest?" Concerns: transformation (raw vs. compiled vs. summarized), storage format (structured markdown, SQLite row, embedded vector, YAML, flat file), trust level (ground truth vs. provisional vs. unverified), and pipeline trigger (manual, event-driven, scheduled, continuous).

**Retrieval** — How knowledge is found and selected when needed. Answers: "Given a need, which knowledge fragments are relevant?" Concerns: selection mechanism (deterministic path lookup, keyword search, semantic similarity, time-range filter, pattern match), scope (what corpus is searched), ranking (how candidates are ordered), and confidence (how certain is the match).

**Injection** — How selected knowledge is delivered into the LLM's context window. Answers: "How and when does this knowledge reach the model?" Concerns: timing (pre-session, on-demand, continuous refresh), placement (system prompt, conversation history, tool result), shaping (raw, summarized, compiled), token budget (how much context space is allocated), and priority (what gets injected first when budget is tight).

### 1.2 The Three Kinds of Knowledge

Not all knowledge behaves the same way. The kind of knowledge determines its natural storage format, its ingestion trigger, its retrieval pattern, and its injection strategy.

**Declarative** — Facts, policies, preferences, decisions, and relationships. Statements about what is true. "We don't service north of Highway 36." "The user prefers PostgreSQL." "Mrs. Johnson prefers Dave." "The CTO persona handles infrastructure questions." Declarative knowledge is the most common kind. It is typically structured, categorical, and version-sensitive (the latest version supersedes prior versions). It maps naturally to indexed storage with deterministic retrieval. A subset of declarative knowledge is **entity-linking** in nature — it connects two entities rather than describing one ("Mrs. Johnson prefers Dave" links a customer to a technician). Entity-linking declarative knowledge benefits from index/registry storage patterns and traversal-based retrieval, but it is epistemically the same as any other declarative fact: a statement about what is true.

**Episodic** — Time-indexed records of what happened. "Last Tuesday we debugged the Nginx config for two hours." "Mrs. Johnson called on April 8th and asked for Dave." "The Q3 planning session produced three action items." Episodic knowledge is narrative, temporal, and accumulative (old episodes don't become invalid, they become history). It maps naturally to time-indexed storage with temporal and associative retrieval.

**Procedural** — Reusable approaches for recurring situations. "When deploying to production, run tests, build the Docker image, then push." "When a caller asks about the rebate, confirm it's still active, then walk through the paperwork." "When the research agent returns results, summarize by theme before passing to the planning agent." Procedural knowledge is the bridge between experience and capability. It is extracted from successful episodes, refined through repeated application, and injected when a matching situation is detected. It maps naturally to pattern-indexed storage (skill files, runbooks, YAML manifests) with pattern-matching retrieval.

---

## 2. The Triage Questions

These questions are asked about a body of knowledge to determine the appropriate ingestion, retrieval, and injection strategies. They are ordered by discriminating power — the primary questions determine the broad architectural category, the secondary questions refine the implementation.

### Primary Triage

**Q1. What kind of knowledge is it?**

| Answer | Ingestion implication | Retrieval implication | Injection implication |
|--------|----------------------|----------------------|----------------------|
| Declarative | Store as structured records (markdown with frontmatter, indexed SQLite rows, YAML). Version-track if updates are expected. For entity-linking facts, consider index/registry storage to support traversal queries. | Deterministic lookup by category/key is preferred. FTS5 as fallback for keyword queries. Vector only if corpus is large and queries are semantically ambiguous. Entity-linking facts benefit from traversal retrieval (given entity A, what is connected to it?). | Inject the current authoritative version. Wholesale injection if volume permits; selective if not. Entity-linking facts often belong in system prompt or agent manifest as structural context. |
| Episodic | Store with timestamp as primary index. Summarize/compile if raw volume is high (compaction). Embed if associative recall is anticipated. | Time-range filter is the primary access pattern. FTS5 for keyword recall. Vector similarity for "that thing we discussed about X" queries. | On-demand only — episodic knowledge is noisy if always injected. Activate on temporal or associative queries. |
| Procedural | Extract from successful workflows (Hermes-style skill creation) or author manually (YAML skill files, runbooks). Store as executable templates with trigger conditions. | Pattern-match: does the current situation match a known skill's trigger conditions? Load skill names/summaries by default; full content on demand. | Inject the matching skill definition into the system prompt when a trigger fires. Keep injection lean — skill name + summary for awareness, full content only when executing. |

**Q2. What is the knowledge volume?**

Volume is assessed per kind, per scope (tenant, user, project). A system may have small declarative knowledge but large episodic knowledge.

| Volume | Threshold | Ingestion implication | Retrieval implication | Injection implication |
|--------|-----------|----------------------|----------------------|----------------------|
| Small | < ~5,000 tokens | Store verbatim. No summarization needed. | No retrieval infrastructure needed — inject everything. | Wholesale injection into system prompt. |
| Medium | ~5,000–50,000 tokens | Store verbatim or lightly structured. Consider categorization to enable selective retrieval. | Deterministic selection (pick the relevant categories) or lightweight search (FTS5). Vector search is optional and rarely justified. | Selective injection — always inject high-signal categories (FAQ, core policies), selectively inject the rest based on context signals (caller ID, query topic). |
| Large | > ~50,000 tokens | Chunking, indexing, and likely embedding at ingestion time. Summarization pipelines for compaction. | Retrieval infrastructure is justified. Layered approach: deterministic first, FTS5 second, vector third. Re-ranking may be warranted. | RAG pattern — retrieve relevant chunks, inject as grounding context. Token budget management is critical. Source attribution becomes necessary. |

**Q3. How dynamic is the knowledge?**

| Dynamism | Description | Ingestion implication | Retrieval implication | Injection implication |
|----------|-------------|----------------------|----------------------|----------------------|
| Static | Changes on human timescales (quarterly, annually). Company policies, product specs, onboarding docs. | Ingest once at setup. Re-ingest on human-initiated update. No automated pipeline needed. | Cache-friendly — retrieval results can be pre-computed and reused across sessions. | Pre-computed injection is safe. No freshness concerns within a session. |
| Interaction-dynamic | Evolves across conversations over time. Learned preferences, FAQ emergence, skill refinement. | Automated pipeline triggered by interaction events. Nightly compilation, post-interaction extraction, compaction at thresholds. | Must query the latest version. Cache invalidation matters. | Injection must reflect the most recent compiled state. Pre-session assembly should read from the latest compiled output. |
| Session-dynamic | Changes during a single conversation. Working memory, conversation state, in-progress reasoning. | Written and read within the session lifecycle. No durable storage unless promoted by a trigger (compaction, fact extraction). | Immediate — lives in the active context window or short-term buffer. | Already in the context window by definition. Management is about pruning (compaction) not injection. |
| Event-driven | Changes in response to external triggers. API updates, webhook notifications, real-time data feeds. | Webhook or polling pipeline. Ingestion is push-based rather than pull-based. | Must be real-time or near-real-time. Staleness tolerance depends on the domain. | Refresh on event. May require mid-session injection if events arrive during a conversation. |

**Q4. What is the provenance?**

| Provenance | Description | Ingestion implication | Retrieval implication | Injection implication |
|------------|-------------|----------------------|----------------------|----------------------|
| Human-authored | The user, business owner, or domain expert provided this directly. Highest trust. | Ingest as ground truth. No confirmation step needed. | Retrieved as authoritative. Wins conflicts with other provenance levels. | Inject without qualification. |
| Interaction-derived | Learned from conversations, calls, or user behavior. Medium trust. | Ingest as provisional until confirmed. Flag for human review if consequence of error is high. Lint against human-authored knowledge for contradictions. | Retrieved with provenance metadata. Source attribution available. | Inject with appropriate confidence. In high-consequence domains, qualify with "based on prior interactions" or similar. |
| Agent-synthesized | The agent compiled, summarized, or inferred this from other knowledge. Lower trust. | Ingest with synthesis metadata (what sources, what method). Subject to periodic review and lint. | Retrieved with synthesis trail. Should not override human-authored knowledge. | Inject as supporting context. Flag when synthesis conflicts with authoritative sources. |
| System-observed | Patterns extracted from behavior — workflow patterns that became skills, frequency-based FAQ emergence, usage statistics. | Ingest when observation thresholds are met (Hermes: 5+ tool calls + success; Wiki PRD: 3+ callers asking the same question). | Retrieved by pattern match against current situation. | Inject when pattern match fires. Confidence proportional to observation count. |

### Secondary Triage

**Q5. What is the temporal relevance pattern?**

| Pattern | Description | Impact on strategy |
|---------|-------------|-------------------|
| Current-state | Only the latest version matters. Old versions are superseded. | Store as mutable records. Retrieval returns the latest. Version history is optional (audit trail, not operational). |
| Historical | Time-indexed recall is the point. Old entries are valuable, not stale. | Store with timestamps as primary index. Retrieval supports time-range filters. Never auto-prune without promotion. |
| Cumulative | Knowledge improves/refines over time. Skills get better with each execution. Facts get more confident with more observations. | Store with refinement metadata (version count, confidence score, last-refined timestamp). Retrieval may weight by confidence or recency. |

**Q6. Who is the consumer?**

| Consumer | Impact on strategy |
|----------|-------------------|
| Single agent | No access control needed. Inject directly. |
| Multiple agents, same tenant | Shared access layer needed. Visibility rules determine which agents see which knowledge (e.g., sector-based: semantic shared, episodic scoped to originating agent). |
| Cross-tenant | Analytics/reporting system, not agent memory. Aggregation and anonymization concerns. Separate from the operational memory system. |
| Human operator | Dashboard, audit, review interface. Knowledge must be human-readable and editable. Markdown/YAML preferred over opaque embeddings. |

**Q7. What is the query pattern?**

| Pattern | Retrieval mechanism |
|---------|-------------------|
| Categorical | Deterministic lookup — file path, index key, SQL WHERE clause, YAML field match. Fastest, most predictable. |
| Associative | Search — FTS5 for keyword, vector cosine similarity for semantic. Appropriate when the query is fuzzy or the user doesn't know the exact terms. |
| Temporal | Time-range filter — SQL WHERE created_at BETWEEN x AND y. Often combined with categorical or associative within the time window. |
| Exhaustive | Full scan within a scope — "give me everything about this customer." Appropriate when the scope is small enough that completeness matters more than selection. |
| Pattern-matching | Skill/procedure lookup — does the current situation match a known trigger? Often involves lightweight classification (keyword triggers, regex, or a cheap LLM call). |

**Q8. What is the acceptable latency?**

| Latency | Constraint | Impact on strategy |
|---------|-----------|-------------------|
| Real-time (< 200ms) | Voice agents, live interactions | Pre-computed injection only. No LLM calls at retrieval time. No vector search unless pre-indexed. Deterministic file/path lookup. |
| Interactive (< 2s) | Chat agents, tool-assisted conversations | On-demand retrieval via tool calls is acceptable. FTS5 and lightweight vector search fit within budget. |
| Deferred (< 30s) | Background enrichment, mid-conversation context loading | Hybrid search (FTS5 + vector + RRF) is fine. LLM-assisted re-ranking is feasible. |
| Batch (minutes+) | Nightly compilation, periodic lint, skill extraction | Full-corpus processing. LLM-driven extraction, summarization, and compilation. Cost optimization over speed. |

**Q9. What is the consequence of stale or wrong knowledge?**

| Consequence | Impact on strategy |
|-------------|-------------------|
| Low | Auto-inject without review. Self-correction through future interactions is acceptable. |
| Medium | Inject with provenance. Flag contradictions. Periodic lint to catch drift. |
| High | Human-in-the-loop confirmation before knowledge enters the authoritative store. Source attribution mandatory at injection. Audit trail for all changes. |

**Q10. What is the expected growth rate?**

| Growth | Description | Impact on strategy |
|--------|-------------|-------------------|
| Bounded | Knowledge stabilizes over time. A plumber's FAQ converges. A personal preference set plateaus. | Design for steady-state volume. Compaction and pruning are housekeeping, not survival mechanisms. |
| Linear | Knowledge grows proportionally to usage. More calls = more episodic records. More projects = more declarative facts. | Plan for storage growth. Tiered storage (hot/warm/cold) becomes relevant at scale. Retrieval must remain efficient as corpus grows. |
| Compounding | Knowledge grows faster than usage. Skill libraries generate derivative skills. Cross-referencing creates new declarative knowledge. | Active pruning, consolidation, and quality management become essential. Without curation, signal-to-noise degrades over time. |

---

## 3. Use Case Profiles

Each use case is a specific combination of triage answers — a clinical presentation that maps to a treatment plan.

### Profile A: Comprehensive Personal Assistant (Brainiac/Atlas)

| Question | Answer |
|----------|--------|
| Q1. Kind | All three: declarative (preferences, decisions, project registry, persona routing — including entity-linking facts), episodic (journal entries), procedural (skills, runbooks) |
| Q2. Volume | Small per kind at any given time. Tier 1 injection budget: ~1,000 tokens. Tier 3 grows unbounded but is queried on-demand. |
| Q3. Dynamism | Mixed. Static (identity, reference docs), interaction-dynamic (extracted facts, journal entries), session-dynamic (conversation history). |
| Q4. Provenance | Primarily human-authored (CLAUDE.md, knowledge bases) and interaction-derived (fact extraction, compaction). Agent-synthesized is minimal. |
| Q5. Temporal | Mixed. Current-state for declarative. Historical for episodic. Cumulative for procedural (skills improve). |
| Q6. Consumer | Single user, multiple personas. Shared declarative, scoped episodic. |
| Q7. Query | Categorical (persona dispatch), associative (Tier 3 recall), temporal (what was I doing last month). |
| Q8. Latency | Interactive (Telegram). Tolerant of 1-2s retrieval. |
| Q9. Consequence | Low to medium. Personal productivity — errors are inconvenient, not catastrophic. |
| Q10. Growth | Linear. Grows with usage but manageable at personal scale. |

**Resulting strategy:**

Ingestion: Dual-write pipeline. After every interaction, a background LLM pass extracts declarative facts (subject-predicate-object) and writes them to both active storage (Tier 1) and long-term storage (Tier 3) with embeddings. Conversation compaction at 30-message threshold produces episodic summaries promoted to Tier 3. Procedural knowledge is manually authored as YAML skill files and markdown runbooks. Entity-linking declarative knowledge is maintained in registries (project manifests, persona configs).

Retrieval: Layered by kind. Declarative retrieval is automatic (FTS5 match against current message, recent memories by recency). Episodic retrieval is on-demand (`/recall` command) using hybrid FTS5 + vector search with RRF fusion and optional time filtering. Procedural retrieval is pattern-matched by command prefix (`/cto`, `/coo`, `/cmo`) or skill trigger keywords. Entity-linking retrieval is deterministic (load project registry, check working directory for satellite DB).

Injection: Automatic lightweight injection at every turn: ~1,000 tokens of recent memories + FTS5 matches + reference doc summaries. Identity (CLAUDE.md) in system prompt permanently. Tier 3 on-demand only — never auto-injected. Procedural knowledge loaded when triggered. Project satellite context loaded based on working directory detection.

### Profile B: Small Business Voice Agent (Plumbing Company)

| Question | Answer |
|----------|--------|
| Q1. Kind | Primarily declarative (policies, service boundaries, pricing, FAQ, customer preferences — including entity-linking such as caller-to-technician preferences). Minimal episodic (transcripts are source material, not directly stored). Procedural is implicit in the agent's system prompt, not a separate knowledge layer. |
| Q2. Volume | Small. Total wiki after months: 5-15 pages, well within 3,000 token injection budget. |
| Q3. Dynamism | Two layers. Static bolus (owner-provided, ingested at onboarding). Interaction-dynamic wiki (compiled nightly from transcripts). |
| Q4. Provenance | Bifurcated. Bolus is human-authored (owner). Wiki is interaction-derived with owner-confirmation as trust escalation. |
| Q5. Temporal | Current-state. The agent needs the latest policies, not the history of how they changed. |
| Q6. Consumer | Single agent (Aria). Single tenant. |
| Q7. Query | Categorical. Known file paths (FAQ, service area, scheduling policies). Caller-specific lookup by ID. |
| Q8. Latency | Real-time. Voice agent — injection must be pre-computed before the caller connects. |
| Q9. Consequence | Low to medium. Bad customer experience is recoverable. Wrong pricing could be problematic. |
| Q10. Growth | Bounded. The wiki stabilizes. A plumber's operational knowledge converges. |

**Resulting strategy:**

Ingestion: Two separate pipelines. The static bolus is ingested once at onboarding from owner-provided documents. The learned wiki is compiled nightly by an LLM batch job that reads new transcripts, extracts durable knowledge, deduplicates against existing pages, and writes/updates structured markdown files with frontmatter. Compilation priorities are ordered: owner corrections > repeated questions > customer preferences > service boundaries > pricing. No embeddings at ingestion — volume doesn't justify it.

Retrieval: Deterministic file-system lookup. `Path.exists()` and `read_text()`. No search engine. FAQ always loaded. Policies always loaded. Caller-specific page loaded by caller ID match. Future fallback: `tool-query` for questions outside injected pages (Phase 3).

Injection: Pre-session wholesale. Before the caller connects, `assemble_wiki_context()` reads relevant files and prepends to system instruction. Hard cap at 3,000 tokens. Zero LLM calls at injection time. Zero vector lookups. Deterministic, fast, predictable.

### Profile C: Multi-Agent Framework (Paperclip-style)

| Question | Answer |
|----------|--------|
| Q1. Kind | All three, with procedural as the highest-value durable output. Declarative (user preferences, project context, agent capability routing — including entity-linking facts like which agent feeds which). Episodic (what happened in this pipeline run). Procedural (workflow patterns that succeeded — the Hermes insight). |
| Q2. Volume | Variable. Inter-agent message passing can be high-volume within a session. Durable knowledge (extracted procedures, global facts) is small to medium. |
| Q3. Dynamism | Session-dynamic (pipeline state during execution). Interaction-dynamic (procedural knowledge refined across runs). Static (agent definitions, capability manifests). |
| Q4. Provenance | Mixed. User directives are human-authored. Agent outputs are agent-synthesized. Extracted skills are system-observed. Trust hierarchy: user directives > confirmed agent outputs > inferred patterns. |
| Q5. Temporal | Current-state for pipeline execution. Cumulative for procedural knowledge (skills improve over time). Historical for audit/review. |
| Q6. Consumer | Multiple agents, same tenant. Shared global memory. Agent-scoped working state. |
| Q7. Query | Categorical (agent routing — which agent handles this task). Pattern-matching (does this task match a known skill). Pass-through (output of agent A becomes input to agent B). |
| Q8. Latency | Interactive to deferred. User is waiting for pipeline completion, but individual agent-to-agent handoffs tolerate seconds. |
| Q9. Consequence | Medium. Wasted tokens and time from poor routing. Low for personal use; higher for business-critical workflows. |
| Q10. Growth | Compounding for procedural knowledge. Skills beget skills. Linear for episodic (run logs). Bounded for declarative. |

**Resulting strategy:**

Ingestion: Three distinct streams. (1) Pipeline state is ephemeral — held in memory during execution, not persisted unless the run succeeds and a skill extraction trigger fires. (2) Declarative facts (user preferences, project context) are extracted and stored in a shared global memory accessible to all agents. (3) Procedural knowledge is extracted post-completion when observation thresholds are met (non-trivial workflow, 5+ tool calls, error recovery, user correction). Skills are stored as structured templates with trigger conditions and execution steps.

Retrieval: Agent routing uses deterministic manifest lookup (capability matching). Skill retrieval uses pattern-matching against the current task description — lightweight keyword triggers first, LLM classification as fallback. Global memory retrieval for cross-agent facts uses FTS5 or deterministic lookup. Inter-agent data passing is direct (output → input), not retrieved from a store.

Injection: Agent context is assembled per-hop: system prompt (agent identity + relevant skills) + global memory excerpt + upstream outputs (shaped/summarized, not raw). The critical optimization is **shaping** — summarize upstream agent outputs before injecting into the next agent's context. A 5,000-token research report should become a 500-token summary for the planning agent. This is where Paperclip-style frameworks burn tokens: they pass full outputs without shaping. Procedural knowledge (matching skills) is injected into the system prompt when a trigger fires.

### Profile D: Enterprise Deployment (Hospital System, Law Firm)

| Question | Answer |
|----------|--------|
| Q1. Kind | All three at scale. Massive declarative corpus (policies, regulations, product catalogs, case law — including complex entity-linking: org structure, policy dependencies, regulatory cross-references). Growing episodic (case notes, interaction logs, audit trails). Procedural (department-specific workflows, approval chains). |
| Q2. Volume | Large. Tens of thousands of documents, potentially millions of knowledge fragments. Far exceeds any injection budget. |
| Q3. Dynamism | Mixed. Core policies are static-ish (regulatory cycle). Active cases and operational data are interaction-dynamic. Compliance requirements may be event-driven (new regulation published). |
| Q4. Provenance | Institutional — multiple authors, departments, approval chains. Version-controlled with formal review processes. Some interaction-derived (case notes, clinical observations). |
| Q5. Temporal | Mixed. Current-state for active policies and procedures. Historical for case records and audit trails (legal requirement). Cumulative for institutional learning. |
| Q6. Consumer | Multiple agents, multiple departments, multiple roles. Complex access control (not all knowledge is visible to all agents/users). Cross-tenant only for benchmarking/analytics. |
| Q7. Query | All patterns. Categorical for known document types. Associative for research queries across the corpus. Temporal for case history. Exhaustive for compliance audits. Pattern-matching for workflow automation. |
| Q8. Latency | Variable by use case. Real-time for clinical decision support. Interactive for research queries. Batch for compliance audits and reporting. |
| Q9. Consequence | High. Legal, medical, financial, regulatory. Source attribution mandatory. Audit trail mandatory. Human-in-the-loop for high-stakes decisions. |
| Q10. Growth | Linear to compounding. Institutional knowledge grows continuously. Without active curation, signal-to-noise degrades. |

**Resulting strategy:**

Ingestion: Industrial-grade pipeline. Automated document processing with chunking, indexing, and embedding at ingestion time. Structured metadata extraction (document type, department, approval status, effective date, supersedes). Version control with full audit trail. Multiple embedding models may be warranted for different document types (clinical notes vs. legal documents vs. policy manuals have different semantic spaces). Quality gates before knowledge enters the authoritative store — human review for high-consequence domains.

Retrieval: Layered retrieval with fallback chain. (1) Deterministic first — if the query maps to a known document category or policy number, go straight to it. (2) FTS5 keyword search — precise matches on policy numbers, procedure names, product codes, medical terminology. (3) Vector similarity — semantic search for ambiguous or exploratory queries. (4) LLM-assisted re-ranking — when the candidate set is large, use a lightweight model to rank by relevance before injection. Retrieval must respect access control — not all knowledge is visible to all consumers.

Injection: RAG pattern. Retrieve relevant chunks, inject as grounding context with source attribution. Token budget management is critical — the corpus is large enough that naive retrieval returns too much. Confidence scoring determines injection priority. Source citations are mandatory in the agent's response. For procedural knowledge, department-specific workflow definitions are injected based on the agent's role and the task type.

---

## 4. Decision Flowchart

For a new knowledge domain, walk through this sequence:

```
START
  │
  ├─ Q1: What kind of knowledge?
  │    ├─ Declarative ──→ Favor structured storage, deterministic retrieval
  │    │    └─ Entity-linking? → Consider index/registry storage, traversal retrieval
  │    ├─ Episodic ─────→ Favor time-indexed storage, temporal/associative retrieval
  │    └─ Procedural ───→ Favor skill templates, pattern-matching retrieval
  │
  ├─ Q2: What volume?
  │    ├─ Small ────────→ Wholesale injection. Skip retrieval infrastructure.
  │    ├─ Medium ───────→ Selective injection. Lightweight retrieval (FTS5, categories).
  │    └─ Large ────────→ RAG pattern. Full retrieval infrastructure. Embeddings justified.
  │
  ├─ Q3: How dynamic?
  │    ├─ Static ───────→ Ingest once. Pre-compute injection. Cache freely.
  │    ├─ Interaction ──→ Automated pipeline (nightly compile, post-interaction extract).
  │    ├─ Session ──────→ In-context management (compaction, pruning). No durable store needed.
  │    └─ Event-driven ─→ Push-based ingestion. Refresh injection on event.
  │
  ├─ Q4: What provenance?
  │    ├─ Human-authored ──→ Ground truth. No confirmation needed.
  │    ├─ Interaction-derived → Provisional. Lint against authoritative sources.
  │    ├─ Agent-synthesized ──→ Lower trust. Review pipeline. Synthesis metadata.
  │    └─ System-observed ────→ Threshold-based ingestion. Confidence scoring.
  │
  └─ Q5-Q10: Refine implementation details
       (temporal pattern, consumer scope, query pattern,
        latency, consequence, growth rate)
```

---

## 5. Anti-Patterns

**The Vector-Everything Fallacy.** Embedding all knowledge at ingestion and using vector similarity for all retrieval. Vector search is a specific tool for a specific problem: semantically ambiguous queries over a large heterogeneous corpus. For small, structured, categorical knowledge, it is unnecessary overhead that adds latency, cost, and complexity without improving results. Most agent knowledge domains are small enough that deterministic injection or FTS5 keyword search outperforms vector retrieval.

**The Deep Hierarchy Fallacy.** Modeling agent delegation as a deep org chart where manager agents delegate to worker agents. Every delegation hop pays the full context-window tax: the manager must describe the task, the worker must re-ingest context, the manager must interpret the result. This is where frameworks like Paperclip burn tokens. The alternative: a single runtime with selective knowledge injection, where different "agents" are the same LLM with different knowledge boluses.

**The Ephemeral Workflow Fallacy.** Treating multi-agent pipeline state as disposable after completion. The data flowing through the pipeline may be ephemeral, but the workflow pattern — the sequence of steps, the approach that worked, the adaptations made when things went wrong — is procedural knowledge that should be captured and refined. Discarding it forces the system to re-derive successful approaches from scratch every time.

**The Retrieval-Over-Compilation Fallacy.** Investing in sophisticated retrieval infrastructure (re-ranking, vector search, hybrid fusion) while under-investing in knowledge compilation quality. A perfectly retrieved fragment from a poorly compiled knowledge base is still garbage. For domains where compilation is feasible (bounded volume, structured output), investing in compiler quality pays higher dividends than investing in retrieval sophistication. A well-curated wiki with file-path lookup beats a messy vector store with state-of-the-art retrieval.

**The Universal Architecture Fallacy.** Using the same memory architecture for all use cases. A personal assistant, a voice agent, a multi-agent framework, and an enterprise deployment have fundamentally different profiles across the triage questions. The triage exists precisely to match the architecture to the profile, not to force all profiles into one architecture.

---

## 6. Key Principles

**Compilation over retrieval when volume permits.** If the knowledge domain is small enough to compile into a curated artifact (a wiki, a FAQ page, a skill file), do the hard work at write time so that read time is trivial. Reserve retrieval infrastructure for domains where compilation isn't feasible.

**Match the mechanism to the query pattern.** Categorical queries deserve deterministic lookup. Associative queries deserve search. Temporal queries deserve time-range filters. Don't use vector search for categorical queries or time-range filters for associative queries.

**Separate provenance layers.** Keep human-authored knowledge separate from interaction-derived knowledge separate from agent-synthesized knowledge. This enables conflict detection, trust hierarchies, and targeted correction. Mixing provenance in a single store loses the ability to reason about where knowledge came from and who can correct it.

**Procedural knowledge is the compounding asset.** Facts and episodes accumulate linearly. Skills compound — a successful workflow pattern accelerates every future instance of that task type, and can be shared across agents or tenants. Investing in skill extraction and refinement produces non-linear returns.

**Shape before injecting.** The token budget is finite. Raw knowledge is almost never the right injection format. Summarize upstream outputs before passing them downstream. Compile transcripts into wiki pages. Distill episodic histories into journal entries. The shaping step is where most token savings and quality gains live.

**Volume is the primary branch point.** Below the injection threshold (~5,000 tokens), skip retrieval entirely and inject everything. Above it, the other triage questions determine which retrieval mechanism is appropriate. Most niche agent deployments live below this threshold and never need retrieval infrastructure.

**Resolve conflicts at write time, not retrieval time.** When a compilation or extraction pipeline produces a fact that contradicts an existing knowledge entry, the conflict must be resolved during ingestion -- not deferred to retrieval or lint. The compiler should compare each extracted fact against the existing knowledge store and make an explicit decision: update the existing entry (if the new fact supersedes it), flag for human review (if provenance is ambiguous or consequence is high), or discard (if the new fact is lower-trust than the existing one). The provenance hierarchy (Q4) determines which source wins. Storing contradictory facts and hoping retrieval sorts them out is how knowledge bases degrade silently. Lint catches what write-time resolution misses, but it is the safety net, not the primary mechanism.

**Make extraction prompts a configurable artifact, not hardcoded logic.** When an LLM extracts knowledge from raw material (transcripts, documents, interaction logs), the extraction prompt determines what gets captured and what gets discarded. This prompt should be a per-scope configurable artifact -- a template with domain-specific instructions, priority ordering, and few-shot examples of what "good extraction" looks like for that domain. A plumbing company's extraction prompt prioritizes service boundaries and pricing; a dental practice's prioritizes insurance acceptance and procedure descriptions; a law firm's prioritizes case outcomes and precedent citations. Hardcoding extraction priorities into the compiler assumes all domains have the same signal profile. They don't. The extraction prompt is a first-class configuration surface, on par with the agent manifest and system prompt.

---

## 7. Applied Architecture: Atlas V2

Atlas V2 is the second generation of the Brainiac personal assistant, built on a four-tier memory architecture. This section maps each tier to the knowledge strategy framework, validating the existing design against the triage questions and identifying where the framework confirms, refines, or extends the current approach.

### 7.1 Tier Mapping

| Tier | Storage | Knowledge Kind(s) | Volume | Dynamism | Provenance | Retrieval | Injection |
|------|---------|-------------------|--------|----------|------------|-----------|-----------|
| Tier 1 — "The Self" | `store/atlas.db` | Declarative (`sector: semantic`) + Episodic (`sector: episodic`) | Small (kept lean by compaction) | Interaction-dynamic (fact extraction), Session-dynamic (conversation history) | Interaction-derived | FTS5 match + recency sort, automatic | Auto-inject ~1,000 tokens per turn |
| Tier 1.5 — "The Manual" | Persona directories (Markdown + YAML) | Declarative | Small per persona | Static | Human-authored | Deterministic file read | On-demand by agent |
| Tier 1.5b — "The Rolodex" | Project reference files + `projects` table | Declarative (entity-linking subtype) | Small | Static | Human-authored | Categorical lookup, FTS triggers | Passive awareness via summaries; deep context on `/project` command |
| Tier 2 — "The Work" | `.atlas/context.db` per project workspace | Declarative (project-scoped) | Small per project | Mixed (static ATLAS_CLAW.md + interaction-dynamic extracted facts) | Mixed (human-authored instructions + interaction-derived facts) | Deterministic (working directory detection) | Auto-inject when `cwd` is inside a project workspace |
| Tier 3 — "The Journal" | `store/long-term.db` | Declarative (`sector: semantic/fact`) + Episodic (`sector: episodic`) | Growing (unbounded by design) | Interaction-dynamic (populated by compaction and fact extraction) | Interaction-derived + System-generated | Hybrid FTS5 + vector cosine similarity with RRF fusion | On-demand only (`/recall` command) |
| Skills | YAML skill files + skill-creator infrastructure | Procedural | Small (bounded skill set) | Static (manually authored, not self-annealing) | Human-authored | Pattern-match (keyword triggers, prefix dispatch) | Inject matching skill definition on trigger |

### 7.2 Framework Validation

**What the framework confirms:**

The tier separation is sound. Each tier occupies a distinct position in the triage space — different combinations of volume, dynamism, provenance, and query pattern. The tiers are not hierarchical in the traditional cache-hierarchy sense; they are parallel knowledge stores optimized for their specific profiles. The numbering suggests "closer vs. farther," but the framework reveals the real organizing principle is "different knowledge profiles require different treatment."

The cross-persona visibility rules (semantic shared, episodic scoped) are a retrieval-time implementation of the framework's consumer question (Q6). The `sector` field is doing double duty: it encodes both knowledge kind (declarative vs. episodic) and visibility scope. This is efficient for a single-user system where the discrimination is simple.

The retrieval budget (~1,000 tokens, ~8 items for Tier 1 auto-injection) is a correctly conservative injection strategy. It keeps the context window lean for reasoning while providing enough grounding for continuity.

The Tier 3 hybrid search (FTS5 + vector with RRF) is justified because the query pattern is genuinely associative and temporal. This is the one tier where the query pattern — not the volume — demands search infrastructure. "What did I decide about deployment strategy three months ago?" requires fuzzy matching across a growing corpus of journal entries where exact keywords may not be recalled.

The `is_universal` flag on fact extraction that routes universal facts to Tier 1 and project-specific facts to Tier 2 satellites is an ingestion-time triage decision — answering Q6 (consumer scope) at extraction time to determine storage location.

**What the framework refines:**

Tier 1 mixes declarative and episodic knowledge in the same store, discriminated by `sector`. The framework notes these have different temporal relevance patterns (Q5): declarative facts are current-state (the latest version supersedes), while episodic summaries are historical (old entries are valuable, not stale). In practice this is handled correctly by the compaction-and-promote lifecycle — episodic entries in Tier 1 are near-term history that eventually moves to Tier 3 for long-term recall. The framework doesn't suggest separating them into different stores (the volume doesn't justify it), but it does clarify *why* they coexist: both need hot-path access for near-term continuity, and the sector field provides sufficient discrimination for retrieval.

Tier 3 holds both declarative (semantic/fact) and episodic records. The framework suggests these might benefit from different indexing strategies within the same database: episodic queries should always be time-filtered first (temporal access pattern), while semantic queries may scan all time (associative access pattern). The current `idx_memories_time` index on `(created_at, sector, persona)` supports both, but query logic should default to time-filtering for episodic retrieval and full-scan for semantic retrieval.

**What the framework identifies as a future extension point:**

Procedural knowledge is currently static and human-authored. The framework's triage would classify a self-annealing skill system as: system-observed provenance, cumulative temporal relevance, pattern-matching retrieval, and interaction-dynamic ingestion. This is a meaningful architectural addition if Atlas's task space expands to the point where manually authoring skills becomes a bottleneck. The current static approach is correct for the current scope — the framework explicitly notes that procedural accumulation is a function of how open-ended the agent's task space is, not a universal requirement.

### 7.3 Data Flow Summary

```
User interaction via Telegram
    │
    ├─► Session context (Tier 1 conversation_events)
    │     └─ Compaction at 30 messages ─► Journal Entry
    │           ├─ Tier 1 (episodic, near-term)
    │           └─ Tier 3 (episodic, long-term, with embedding)
    │
    ├─► Background fact extraction (fire-and-forget LLM pass)
    │     ├─ is_universal? ─► Tier 1 (semantic, all-persona visible)
    │     └─ project-specific? ─► Tier 2 satellite
    │     └─ Both ─► Tier 3 (with embedding, conflict detection)
    │
    ├─► Prefix dispatch (/cto, /coo, /cmo)
    │     └─ Load persona identity + Tier 1.5 knowledge base
    │
    ├─► Working directory detection
    │     └─ Load Tier 2 satellite if .atlas/ exists
    │
    └─► /recall command (on-demand)
          └─ Tier 3 hybrid search (FTS5 + vector, RRF fusion)

Context assembly per turn:
    System prompt: ATLAS_CLAW.md (identity)
    + Auto-injected: ~1,000 tokens (FTS5 matches + recent memories + reference summaries)
    + Conditional: Tier 2 satellite (if in project workspace)
    + Conditional: Skill definition (if trigger matches)
    + On-demand: Tier 3 results (if /recall invoked)
```

---

## 8. Applied Architecture: AI Labor Solutions

AI Labor Solutions is a multi-tenant agency automation platform built on a LangGraph architecture. Each tenant gets an isolated agent with tenant-specific knowledge, but the runtime, ingestion subgraphs, and retrieval mechanisms are shared platform infrastructure. This section applies the knowledge strategy framework to define the per-tenant knowledge architecture and the platform-level knowledge services.

### 8.1 Design Constraints

**Multi-tenant isolation.** Each tenant is a hard knowledge boundary. No knowledge crosses tenant boundaries in the operational system. Platform-level intelligence (cross-tenant analytics) is a separate concern mined from tenant stores behind the scenes, not a shared memory layer.

**Niche agent scope.** Tenant agents are purpose-built for bounded task sets (voice bot with 3-5 skills, chat agent for appointment scheduling, etc.). The agent's task space is narrow and well-defined at deployment time. Procedural knowledge is authored at deployment, not learned — the procedures are deterministic workflows, not emergent patterns.

**Auto-deployable.** The knowledge framework must support automated provisioning. When a new tenant is onboarded, the platform generates the knowledge structure from the onboarding process without manual configuration beyond initial setup.

**LangGraph subgraph architecture.** Ingestion and retrieval are implemented as LangGraph subgraphs that agents opt into via manifest declaration. Not all agents use all subgraphs — a new tenant with no transcripts yet doesn't need the wiki compilation subgraph.

### 8.2 Per-Tenant Knowledge State

Each tenant's knowledge consists of four components, all stored in the tenant's isolated directory:

**Static Bolus** — Owner-provided business knowledge ingested at onboarding.

| Triage Question | Answer |
|-----------------|--------|
| Kind | Declarative |
| Volume | Small (business description, services, policies — typically under 2,000 tokens) |
| Dynamism | Static (re-ingested on owner-initiated update) |
| Provenance | Human-authored (business owner) — highest trust |
| Temporal relevance | Current-state |
| Consumer | Single tenant agent |
| Query pattern | N/A — injected wholesale |
| Latency | Pre-computed (assembled before session) |
| Consequence | Medium (wrong business info = bad customer experience) |
| Growth | Bounded |

Ingestion: Owner provides documents/answers during onboarding. Platform processes into structured storage (SQLite or structured markdown). Re-ingest on owner update via dashboard.

Retrieval: None needed — volume is small enough for wholesale injection.

Injection: Pre-session, wholesale, into system instruction.

**Learned Wiki** — Institutional knowledge compiled from customer interactions.

| Triage Question | Answer |
|-----------------|--------|
| Kind | Declarative |
| Volume | Small (5-15 pages after months of operation, within 3,000 token injection budget) |
| Dynamism | Interaction-dynamic (compiled on schedule from transcripts) |
| Provenance | Interaction-derived, with owner-confirmation as trust escalation |
| Temporal relevance | Current-state (latest compiled version supersedes) |
| Consumer | Single tenant agent |
| Query pattern | Categorical (FAQ, service area, caller preferences — known file paths) |
| Latency | Pre-computed (compiled in batch, assembled before session) |
| Consequence | Low to medium |
| Growth | Bounded (converges as the business's operational knowledge stabilizes) |

Ingestion: Nightly (or N-transcript-triggered) LLM batch compilation. Reads new transcripts since last compile, reads existing wiki, extracts durable knowledge, deduplicates, writes/updates structured markdown. Compilation priorities: owner corrections > repeated questions > customer preferences > service boundaries > pricing.

Retrieval: Deterministic file-system lookup. `Path.exists()` + `read_text()`. No search infrastructure.

Injection: Pre-session wholesale. `assemble_wiki_context()` reads relevant files and prepends to system instruction. Hard cap at 3,000 tokens. Zero LLM calls at injection time.

**Agent Skills** — Deterministic procedures for the agent's bounded task set.

| Triage Question | Answer |
|-----------------|--------|
| Kind | Procedural |
| Volume | Small (3-5 skills for a typical niche agent) |
| Dynamism | Static (authored at deployment, not learned) |
| Provenance | Human-authored (platform developer or deployment engineer) |
| Temporal relevance | Current-state |
| Consumer | Single tenant agent |
| Query pattern | Pattern-match (skill triggers defined in manifest) |
| Latency | Pre-computed (loaded at session start as part of system prompt) |
| Consequence | Low (skill failure = graceful fallback to general agent behavior) |
| Growth | Bounded (new skills added by platform, not by agent self-improvement) |

Ingestion: Authored as skill definitions during agent deployment. Stored as structured config in the agent manifest or as separate skill files referenced by manifest.

Retrieval: Pattern-match against manifest-defined triggers, or always-loaded if the skill set is small enough.

Injection: Included in system prompt at session start. For a 3-5 skill agent, all skill definitions fit within the token budget alongside the bolus and wiki.

**Agent Manifest** — The deployment configuration that ties everything together.

| Triage Question | Answer |
|-----------------|--------|
| Kind | Declarative (entity-linking subtype — connects agent to knowledge sources, skills, and injection strategies) |
| Volume | Small (single YAML file) |
| Dynamism | Static (changes only on re-deployment or configuration update) |
| Provenance | Human-authored (platform or deployment engineer) |
| Temporal relevance | Current-state |
| Consumer | Platform runtime |
| Query pattern | Categorical (read manifest, follow declarations) |
| Latency | Pre-computed (read at agent initialization) |
| Consequence | High (wrong manifest = wrong agent behavior for all sessions) |
| Growth | Bounded |

Ingestion: Generated during onboarding or authored by deployment engineer. Declares knowledge sources, skill bindings, injection strategies, and token budgets.

Retrieval: Direct file read at agent initialization.

Injection: The manifest is not injected into the agent — it instructs the platform on *how* to assemble the agent's context. It is metadata about injection, not injected knowledge itself.

### 8.3 Platform-Level Knowledge Services (LangGraph Subgraphs)

These are shared infrastructure subgraphs that tenants opt into via manifest declaration:

**Bolus Ingestion Subgraph** — Processes owner-provided documents into the tenant's structured knowledge store. Activated at onboarding and on owner-initiated updates. Handles document parsing, structuring, and storage. Available to all tenants.

**Wiki Compilation Subgraph** — Reads new transcripts, compiles durable knowledge into wiki pages. Activated on schedule (nightly, or after N new transcripts). Handles transcript reading, LLM extraction, deduplication against existing wiki, page creation/update. Available to tenants with active transcript accumulation. Skipped for tenants with no new transcripts since last compile (hash-based change detection). Conflict resolution happens at write time: the compiler compares each extracted fact against existing wiki pages and the static bolus, resolving by provenance hierarchy (owner corrections supersede interaction-derived facts, which supersede agent-synthesized observations). Unresolvable conflicts are flagged for owner review via the escalation channel. The extraction prompt is loaded from a per-tenant configurable template (`extraction_prompt.md` in the tenant's wiki directory), allowing domain-specific extraction priorities and few-shot examples. A default template is provided at onboarding and can be refined by the platform or business owner.

**Pre-Session Assembly Subgraph** — Reads the tenant manifest, assembles the knowledge payload for a new session. Reads bolus, wiki, and skill definitions. Respects token budget declarations. Outputs the assembled system instruction. Activated at every session start. Deterministic, zero LLM calls.

**Wiki Query Subgraph** (future) — Tool-call interface for mid-session knowledge retrieval. For questions outside the pre-session injected pages. Activated when the agent invokes the `query_learned_knowledge` tool. Available when the platform supports mid-session tool calling (e.g., Gemini Live async tool calling).

**Lint Subgraph** (future) — Structural and cross-layer health checks. Flags contradictions between wiki and bolus. Detects orphaned pages, sparse content, stale entries. Runs on schedule (weekly) or on-demand.

### 8.4 Auto-Deployment Flow

```
New tenant onboarded
    │
    ├─ Onboarding process collects:
    │    ├─ Business information (→ bolus)
    │    ├─ Agent type selection (→ skill set)
    │    └─ Configuration preferences (→ manifest parameters)
    │
    ├─ Platform generates:
    │    ├─ Tenant directory: data/knowledge/{tenant_id}/
    │    ├─ Bolus: data/knowledge/{tenant_id}/bolus/ (processed onboarding docs)
    │    ├─ Wiki directory: data/knowledge/{tenant_id}/wiki/ (empty, awaits first compile)
    │    ├─ Manifest: data/knowledge/{tenant_id}/manifest.yaml
    │    └─ Transcript directory: data/transcripts/{tenant_id}/ (empty, awaits first call)
    │
    ├─ Agent is live:
    │    ├─ Pre-session assembly reads manifest + bolus
    │    ├─ Wiki injection skipped (no wiki pages yet)
    │    └─ Skills loaded from manifest
    │
    └─ After first transcripts accumulate:
         └─ Wiki compilation subgraph activates on next scheduled run
              └─ Wiki pages created, injected on subsequent sessions
```

### 8.5 Manifest Example

```yaml
tenant_id: johnson-plumbing
agent_type: voice-inbound
model: gemini-2.5-flash

knowledge:
  bolus:
    path: "{tenant_id}/bolus/"
    format: sqlite           # or markdown
    description: "Static company knowledge from onboarding"

  wiki:
    path: "{tenant_id}/wiki/"
    injection_strategy: pre-session
    max_injection_tokens: 3000
    compilation:
      trigger: scheduled       # scheduled | n-transcripts
      schedule: "0 22 * * *"   # 10 PM daily
      model: gemini-2.5-flash  # cheaper model for structured extraction
      extraction_prompt: "{tenant_id}/wiki/extraction_prompt.md"  # per-tenant, domain-specific
      conflict_resolution: provenance-hierarchy   # provenance-hierarchy | flag-for-review | newest-wins
      priorities:                                 # default ordering if no custom extraction prompt
        - owner-corrections
        - repeated-questions
        - customer-preferences
        - service-boundaries
        - pricing

skills:
  - skill_id: schedule-appointment
    triggers: [schedule, appointment, booking, available]
  - skill_id: answer-faq
    triggers: [question, how, what, when, where, do you]
  - skill_id: send-email-summary
    triggers: [email, send, summary, follow up]

injection:
  token_budget: 6000          # total for system instruction
  always_inject:
    - bolus
    - wiki/faq/top-questions.md
    - wiki/concepts/service-area.md
    - wiki/concepts/scheduling-policies.md
  conditional_inject:
    - pattern: caller-id-match
      source: wiki/concepts/caller-{caller_id}.md
```

---

## 9. Practical Application Guide

The preceding sections define the triage questions and map them to architectural choices. This section walks through those same choices from a practitioner's perspective -- how you actually think about knowledge when you're standing in front of a system and deciding what goes where.

The key distinction in this section is between **information** and **process**. Most memory system discussions confound the two. Information is what you know -- its type, its truth value, its relevance. Process is how information moves through the system -- how it enters, how it's validated, where it's stored, how it's retrieved, when it's pruned. Getting the information model right without getting the process model right produces a well-organized but stale knowledge base. Getting the process model right without the information model produces a well-maintained pile of junk. Both are required.

### 9.1 Declarative Knowledge

Declarative knowledge is facts, policies, preferences, decisions, and relationships. Statements about what is true. This is the most common kind of knowledge in any agent system and the one most often mishandled.

#### 9.1.1 The Nature of Declarative Facts -- "The Degree on the Wall"

A physician earns an MD. That fact doesn't change. It becomes part of the permanent environment. The same is true for a set of facts that were once dynamic but have now settled: "I learned Python." "I bought a Mac Mini M4 Pro." "The business is located at 123 Main Street." These were events once, but their enduring output is a static declarative fact. The event is episodic; the resulting state is declarative.

Static declarative knowledge is the bedrock layer. It changes on human timescales -- career moves, major purchases, business pivots -- not on interaction timescales. It enters the system through deliberate human action: an onboarding form, a dashboard entry, a CLAUDE.md edit. It is never inferred or extracted from conversation. The human authors it, and it is ground truth.

The triage in Section 2 distinguishes static from interaction-dynamic knowledge as if they are different species. In practice, they are the same species at different life stages. All declarative knowledge was dynamic once. You earned the MD -- that was an event. The event settled into a static fact. You learned Python -- that was a process. The process concluded and left behind a static credential. Life unfolds linearly, and as it does, new declarative facts continuously emerge from experience and need to find their way into the system.

"Dynamic declarative" is therefore not a separate information type. It is the **intake process** -- the mechanism by which new facts are triaged, routed to the appropriate storage location, and placed at the correct level of accessibility. The information itself, once it arrives, is static declarative. The dynamism is in the arrival, not the content. This reframing matters because it shifts the design problem from "how do I store dynamic declarative knowledge differently?" to "what process governs how new facts enter the system?"

#### 9.1.2 The Five Concentric Circles

Not all knowledge has the same proximity to the agent's reasoning. There are five circles, each with a different trust level, accessibility pattern, and governance model. The model applies across all knowledge types (declarative, procedural, episodic) with consistent semantics at each level. Circles 1-3 are knowledge layers (processed, governed). Circles 4 and 5 are source layers (raw material, different origins). The distinction between Circles 4 and 5 is not knowledge type but knowledge source.

**Circle 1 -- The Problem Representation (Always Injected)**

This is the CLAUDE.md layer. It contains the compact, high-signal summary that should be in the context window at all times. Think of it the way a clinician thinks of the one-liner on a patient: the distilled identity that tells you how to orient. "Physician-builder. Solo operator. Python and TypeScript. Mac Mini M4 Pro. Building two products and a personal AI infrastructure." This is always injected. It is the system prompt baseline.

The constraint is token budget -- this layer must stay lean (hundreds to low thousands of tokens) because it is loaded on every turn of every session. Everything in Circle 1 is human-curated and confirmed. It is ground truth. It changes infrequently and only through deliberate human action.

**Circle 2 -- The Reference Library (Never Injected, Retrieved on Demand)**

This is the larger corpus of confirmed declarative facts that don't fit in Circle 1 but are available when needed. The full professional history. The detailed infrastructure inventory. The complete list of subscriptions and their renewal dates. The client roster with contact details. This layer is too large for constant injection but too valuable to discard. It lives in structured storage -- organized by bolus so it can be retrieved deterministically.

Everything in Circle 2 is human-confirmed. It entered either through direct human entry (ground truth) or through the reconciliation process (agent-detected, human-confirmed). Circle 2 content is never pushed into the context window. It is pulled when needed -- by agent self-retrieval, by user direction, or by system trigger. The connection between Circle 1 and Circle 2 is the index function: Circle 1 contains enough information (categorical pointers and trigger keywords) for the agent to know when and where to reach into Circle 2.

**Circle 3 -- The Agent's Observations (Unconfirmed, Retrievable with Lower Trust)**

This is where agent-detected and system-observed facts land before human confirmation. The agent hears "I got a Google Cloud certificate" during conversation and extracts it as a candidate fact. That fact enters Circle 3 -- not Circle 2, because no human has confirmed it. Circle 3 is the knowledge equivalent of a medication reconciliation list: the system's best understanding of what might be true, awaiting clinician review.

Circle 3 is retrievable but carries lower trust than Circle 2. An agent can reference Circle 3 content, but should qualify it: "Based on a prior conversation, you may have a Google Cloud certificate -- is that correct?" Circle 3 content never enters Circle 1 without passing through human reconciliation.

**Circle 4 -- Raw Episodic Capture (Unprocessed Source Material)**

This is where all interactions, transcripts, session records, and call logs land. Circle 4 is undifferentiated source material -- no judgment has been applied, no extraction has been performed. It is the chart before the physician has written the visit note. Its value is as input to the compilation and extraction processes, not as a retrieval target in normal operation.

Circle 4 is the largest layer by volume and the lowest by per-unit retrieval value. A raw conversation transcript is noisy -- full of false starts, tangents, pleasantries, tool call outputs, and low-signal exchanges. Its governance is mostly automated: episodes accumulate without human intervention, and the compilation process reads Circle 4 to produce outputs routed to other circles.

Content moves inward from Circle 4 through two paths:
- **Agent curation (Circle 4 → Circle 3):** The compilation pipeline extracts candidate facts and patterns from raw episodes, depositing them in Circle 3 for reconciliation. The agent applies judgment about what might be worth keeping; the human confirms.
- **Human curation (Circle 4 → Circle 2):** The human reads a transcript or interaction record and directly promotes a fact, insight, or compiled summary to a specific Circle 2 bolus. This bypasses Circle 3 because the human's judgment is ground truth.

Circle 4 also feeds Circle 1's recency context directly: a post-session compilation step reads the latest episode and refreshes the "where things stand" block in the injection file.

The five circles form a trust and processing gradient. Circles 1-3 are knowledge layers (processed, governed). Circles 4 and 5 are source layers (raw material, different origins):

| Circle | Content | Trust Level | Governance | Injected? | Retrieval |
|--------|---------|-------------|------------|-----------|-----------|
| 1 | Injection point -- identity, bolus manifest, recency context, skill manifest | Ground truth | Human-curated only | Yes, every turn | Automatic (system prompt) |
| 2 | Confirmed knowledge boluses (declarative + procedural + compiled episodic + behavioral profile) | Confirmed | Human-entered or human-reconciled | Never | On-demand (pull) |
| 3 | Agent's curation layer -- candidate facts, proposed skills, behavioral patterns | Provisional | Agent-detected, awaiting human reconciliation | Never | On-demand (pull, with qualification at permissiveness 3+) |
| 4 | Episodic capture -- transcripts, interaction logs, session records | Unprocessed | Automated capture (byproduct of agent interaction) | Never | Rarely (audit, recompilation) |
| 5 | Behavioral mining -- micro-pipeline observations from systems outside the agent | Unprocessed | Deliberate deployment (user decides which pipelines run) | Never | Rarely (compilation source) |

The distinction between Circle 4 and Circle 5 is source, not type. Circle 4 accumulates passively as a byproduct of agent interaction. Circle 5 accumulates deliberately because the user deployed observation pipelines to watch specific behaviors in specific systems. The 80/20 curation decision -- which behaviors are worth watching -- is made at Circle 5 deployment time, before a single observation is collected. This is front-end curation: filtering at the source, not after collection.

Knowledge moves inward through the circles via processing and confirmation:
- Circle 5 → Circle 3 (behavioral compilation extracts candidate patterns)
- Circle 4 → Circle 3 (episodic compilation extracts candidate facts)
- Circle 4 → Circle 2 (human curation bypasses Circle 3)
- Circle 5 → Circle 2 (human curation bypasses Circle 3)
- Circle 3 → Circle 2 (human reconciliation confirms)
- Circle 2 → Circle 1 (promotion when knowledge gains orientation value)

Knowledge moves outward through obsolescence, error, or demotion:
- Circle 1 → Circle 2 (demoted when no longer broadly relevant)
- Circle 2 → removed (fact was wrong or superseded)
- Circle 3 → removed (rejected during reconciliation)
- Circle 4 → archived or pruned per retention policy
- Circle 5 → archived or pruned per retention policy

```
              ┌───────────────┐
              │   CIRCLE 1    │
              │   Injection   │   ◄── Single file, always injected
              │   Point       │       Contains pointers to C2 boluses
              │               │       Contains recency context
              └───────┬───────┘       Contains skill manifest
                      │ (pointers)
                      ▼
         ┌────────────────────────┐
         │       CIRCLE 2         │
         │  ┌────┐ ┌────┐ ┌────┐ │
         │  │ B1 │ │ B2 │ │ B3 │ │   ◄── Confirmed knowledge boluses
         │  └────┘ └────┘ └────┘ │       (declarative + procedural +
         │  ┌────┐ ┌────┐       │        compiled episodic + behavioral)
         │  │ B4 │ │ B5 │       │       Human-curated/confirmed
         │  └────┘ └────┘       │       Never injected, retrieved
         └────────────┬──────────┘
                      │
                      │ (reconciliation: C3→C2)
                      │ (human curation: C4/C5→C2)
                      │
         ┌────────────┴──────────┐
         │       CIRCLE 3         │
         │   Agent's Curation     │   ◄── All sources converge here
         │   Layer                │       Front-end curation gate
         │                        │       Permissiveness slider governs
         └──────┬─────────┬──────┘
                │         │
       ┌────────┴──┐  ┌───┴───────────┐
       │  CIRCLE 4  │  │   CIRCLE 5    │
       │  Episodic  │  │   Behavioral  │
       │  Capture   │  │   Mining      │
       │            │  │               │
       │ Byproduct  │  │ Deliberate    │
       │ of agent   │  │ observation   │
       │ interaction│  │ pipelines     │
       │            │  │               │
       │ Transcripts│  │ OS usage      │
       │ Call logs  │  │ App patterns  │
       │ Sessions   │  │ Study habits  │
       └────────────┘  └──────────────┘

  SOURCE LAYERS (4 & 5)     KNOWLEDGE LAYERS (1-3)
  Raw material               Processed, governed
  Different origins          Converge at Circle 3
  Technology per triage      Technology per triage
```

#### 9.1.3 How the Circles Connect

Circle 1 must contain enough information to know *when* to reach into Circle 2, even if it doesn't contain the detail itself. This is the index function. Two patterns:

**Pattern 1: Categorical pointers.** Circle 1 contains a summary line and a path. "Infrastructure: Mac Mini M4 Pro, macdevserver (Ubuntu). Full registry at `sysadmin-infrastructure/registry.json`." The agent reads the summary for orientation. When a question requires detail ("What port is Paperclip running on?"), the agent knows where to look without searching.

**Pattern 2: Trigger keywords.** Circle 1 mentions a domain in passing. "Manages subscriptions across multiple services." The agent recognizes a subscription-related question and knows to invoke the subscription management skill, which loads the Circle 2 detail. Circle 1 doesn't point to a file -- it signals that a capability exists.

Both patterns share the same property: Circle 1 is sufficient for the agent to decide whether it needs more, and sufficient to know where to find it. The agent never searches blindly. Circle 1 is the index; Circle 2 is the content.

The test for what earns Circle 1 placement: *frequency of relevance* and *orientation value*. A fact belongs in Circle 1 if it is relevant to a high percentage of interactions (the user's name, role, and primary tools) or if it fundamentally changes how the agent should behave (the user is a physician, so clinical reasoning analogies land; the user is a solo operator, so don't suggest team-based workflows). Everything else belongs in Circle 2. If you removed this fact from the system prompt, would the agent make worse decisions on a typical interaction? If yes, Circle 1. If "only when that topic comes up," Circle 2.

This mirrors the clinical problem representation. The one-liner includes active problems, relevant history, and decision-relevant findings -- not the complete medical record. The complete record is in the chart, accessible when needed. Putting the entire chart in the one-liner makes it useless; leaving critical findings out of the one-liner makes it dangerous.

#### 9.1.4 Knowledge Boluses -- Plug-and-Play Declarative Sets

Declarative knowledge doesn't arrive as a uniform mass. It arrives in discrete, self-contained units -- what this framework calls **knowledge boluses**. A bolus is a bounded set of knowledge that represents a complete domain competency, credential, or capability profile.

The analogy is biological. A physician has an MD bolus and an MPH bolus plugged into their brain. A neighbor with only an MPH has one bolus, not the other. The MD bolus contains a coherent body of knowledge -- anatomy, pharmacology, clinical reasoning, diagnostic frameworks -- that functions as a unit. You don't have half an MD. You either have the bolus or you don't.

This maps directly to how agent knowledge should be structured. An agent serving a plumbing company has a "plumbing services" bolus and a "local service area" bolus. An agent serving a dental practice has a "dental procedures" bolus and an "insurance acceptance" bolus. The boluses are interchangeable modules -- plug one in, the agent gains that competency; unplug it, the competency is gone. The agent's total knowledge profile is the sum of its plugged-in boluses.

The plug-and-play property has practical implications:

**Composability.** Boluses combine without interference. An agent can have a "company policies" bolus and a "product catalog" bolus and a "customer preferences" bolus. Each is authored, versioned, and maintained independently. Adding a new bolus doesn't require rewriting existing ones.

**Testability.** A bolus can be validated in isolation. Does the agent answer service-area questions correctly with just the service-area bolus loaded? If yes, the bolus is sound. If not, the bolus needs refinement. This is the unit test for knowledge.

**Circle 1 as bolus manifest.** Circle 1 becomes a manifest of which boluses are loaded, with a summary line per bolus and a pointer to the full content. The agent knows its own competency profile by reading the manifest. When a question falls outside the loaded boluses, the agent can say so explicitly rather than hallucinating -- the same way a physician with an MD and MPH knows to refer a patent question to a lawyer rather than guessing.

Each bolus has its own Circle 1 summary (a line in the manifest) and its own Circle 2 content (the full knowledge set). The circles scale horizontally as boluses are added, with Circle 1 growing by one summary line per bolus and Circle 2 growing by one knowledge set.

#### 9.1.5 Single Point of Injection

The industry has developed a proliferation of injection files -- soul files, tone files, persona files, knowledge files, context files -- each injected separately into the context window. This is architecturally wrong. If they're all injected every turn, they're all part of the same injection. If they're not all injected, then the ones that aren't are Circle 2 knowledge that should be retrieved on demand, not injected at all. There is no middle ground that justifies fragmenting the injection across multiple files.

The correct architecture has **one declarative injection file per agent**. Call it the declarative injection, the CLAUDE.md, the AGENTS.md -- the name doesn't matter. What matters is that it is a single artifact that contains everything the agent needs to know on every turn:

- Identity and orientation (who the agent is, who the user is)
- Behavioral constraints (tone, rules, boundaries)
- Bolus manifest (one summary line and one categorical pointer per knowledge bolus)
- Active context signals (trigger keywords, skill summaries, routing rules)

Everything in this file is injected on every turn. Nothing outside this file is injected automatically. The file is Circle 1, fully materialized as a single document. It becomes cached tokens after the first turn of a session -- pay once for the system prompt, amortize across every subsequent turn.

**Only Circle 1 is injected. Circles 2, 3, and 4 are never injected.** This is the key discipline. The knowledge boluses that back an agent live in structured storage. They are never pushed into the context window. They are pulled when needed. The declarative injection file contains the index that makes retrieval possible, but the content stays outside the context window until a specific need brings it in.

This is progressive disclosure applied to knowledge architecture. The agent always knows *what* it knows (the manifest). It only loads *the detail* when a specific interaction demands it.

**The declarative injection file is constant-sized.** It does not grow with the number of facts in the system. It grows only with the number of boluses, and each bolus adds one summary line. As Circle 2 grows in depth (more facts per bolus), the injection file stays the same size. As the number of boluses grows, the process governing what earns a manifest entry becomes more selective, but the file's token budget remains fixed. The scaling challenge is entirely in Circle 2's storage and retrieval mechanisms -- a process concern, not an injection concern.

**Not all boluses appear in every injection.** The manifest is not a complete index of everything in Circle 2. It is the *active subset* -- the boluses relevant to the current agent's purpose. Each bolus carries an activation toggle: active (included in the Circle 1 manifest) or inactive (exists in Circle 2 but excluded from the injection). A system may have 60 boluses in Circle 2 but only 28 active in the manifest for a given agent or context.

This selective activation serves two purposes. First, it is how niche agents are configured. A voice agent for a plumber doesn't need the dental procedures bolus even if both exist in the same Circle 2 store. The manifest includes only what the agent needs. Second, it is the scaling answer to the curation pressure problem (Section 10.3). Instead of agonizing over which boluses deserve a manifest line as the total count grows, the system maintains the full library in Circle 2 and selectively activates boluses per agent, per context, or per session.

The mature version of this is **dynamic manifest assembly**: the system evaluates the current context (which agent, which user, what topic, what session history) and assembles the Circle 1 manifest on the fly from the available boluses. A conversation about infrastructure activates the infrastructure bolus; a conversation about theology activates a different set entirely. Memory becomes responsive to how it is used, not a static declaration of everything the agent might ever need. This is a future capability -- Phase 1 uses static activation toggles configured per agent. But the architecture should not preclude dynamic assembly, and the bolus metadata should include the fields (tags, categories, activation rules) that a future routing system would consume.

**The dynamic component is upstream of injection, not inside it.** Compilation, reconciliation, and promotion are processes that change what's in the circles. Injection is the simple act of loading Circle 1 into the context window. These are separate concerns. The declarative injection file changes infrequently (when Circle 1 is updated through the intake process). The Circle 2 boluses change more often (as new facts are confirmed through reconciliation). But injection itself is simple and static within a session: load the one file, cache it, use it every turn.

#### 9.1.6 The Intake Process

Every agent system needs an intake pipeline, not just a storage layer. Most systems invest in how knowledge is stored and retrieved but ignore how new knowledge enters the system in the first place. The intake process -- the routing of new facts into the right bolus at the right circle level through the right trust path -- is the mechanism that keeps the knowledge base current without letting it degrade.

**Three entry points feed the intake process:**

*Human-initiated.* The user opens a dashboard or form and enters the fact deliberately. "I completed my Python certificate on March 15." This is the highest-trust intake path. The human has already triaged the fact as worth recording and is providing it in structured form. Route directly to Circle 2 (or Circle 1 if orientation-critical) with ground-truth provenance.

*Agent-detected.* The agent notices a new fact during conversation or extracts it from Circle 4 episodic records during compilation. "Got a Google Cloud certificate." "Switched to a new phone number." These candidate facts enter Circle 3 -- the agent's curation layer, awaiting human confirmation.

*System-observed.* A pipeline or integration detects a state change. A new device appears on the network. A subscription renewal email arrives. These candidate facts also enter Circle 3, awaiting human confirmation.

**Three decisions route each fact:**

*Decision 1: Which bolus?* A Python certificate belongs in a "technical skills" bolus. A new Mac Mini belongs in an "infrastructure" bolus. Some facts clearly belong to an existing bolus. Others may signal the need for a new bolus entirely. The intake process must handle both.

*Decision 2: Which circle?* Human-initiated facts go directly to Circle 1 or Circle 2 (human decides). Agent-detected and system-observed facts go to Circle 3 first, then to Circle 2 through reconciliation, then potentially to Circle 1 through promotion. Raw episodic content (transcripts, logs) goes to Circle 4, where it feeds Circle 3 through agent compilation or Circle 2 through direct human curation.

*Decision 3: Does this contradict existing knowledge?* Resolved at write time per Section 6: human-authored supersedes interaction-derived. Unresolvable conflicts are flagged for human review.

#### 9.1.7 The Medication Reconciliation Model

The right model for moving facts from Circle 3 to Circle 2 comes from clinical medicine: **medication reconciliation**. When a patient arrives at a hospital, the system generates a list of medications it believes the patient is taking -- assembled from pharmacy records, prior visits, insurance claims. The clinician doesn't blindly accept this list. They sit down with the patient and reconcile: "Are you still taking this? Did your dose change? Any new medications?" The system proposes; the human confirms.

Apply this to declarative knowledge intake:

**The agent extracts to Circle 3, but does not promote.** During conversation, the agent identifies candidate declarative facts and writes them to Circle 3 with source attribution (which conversation, what date, what the user actually said).

**The human reconciles on their own schedule.** The dashboard presents Circle 3 facts for review. Each fact gets three options: confirm (promotes to Circle 2, routed to the appropriate bolus), reject (removed from Circle 3), or defer (stays in Circle 3 for later review).

**The reconciliation interface should be lightweight.** A list of candidate facts, each one or two lines, with a bolus suggestion. Confirm, reject, defer. The agent handles volume; the human handles judgment.

**The permissiveness slider.** Not all systems need the same level of human gating. The framework supports a configurable permissiveness level that governs how much latitude the agent has in Circle 3:

| Level | Behavior | Appropriate When |
|-------|----------|-----------------|
| 1 (Restrictive) | Agent stages all candidate facts for human review before they enter Circle 3. Nothing is retrievable until reviewed. | New system, building trust. High-consequence domain. Weaker model. |
| 2 | Agent writes to Circle 3 automatically, but Circle 3 is not consulted during retrieval until facts are reconciled to Circle 2. | Default starting position for most systems. |
| 3 | Agent writes to Circle 3 automatically, and Circle 3 content is retrievable (with provenance qualification). Reconciliation happens on the human's schedule. | Moderate trust established. Low-consequence domain. Strong model. |
| 4 | Agent auto-promotes low-consequence facts to Circle 2 (e.g., tool preferences, minor technical details). High-consequence facts (identity, credentials, relationships) still require reconciliation. | High trust. Strong model. Human reviews periodically. |
| 5 (Permissive) | Agent has wide latitude. Most facts auto-promote to Circle 2. Human reviews are rare and focus on Circle 1 changes and contradictions. | Maximum trust. Strongest models. Human spot-checks. |

Permissiveness is a function of two independent variables: **human trust** (built through experience with the system -- seeing the agent make correct extraction decisions builds confidence) and **model capability** (newer, larger models make fewer extraction errors than older, smaller ones). A physician doesn't trust a medical student the same way they trust a fellow attending. The permissiveness setting should reflect both factors. A dashboard slider makes this explicit rather than implicit.

The permissiveness level is a human-managed setting. The system does not auto-adjust its own permissiveness. Trust is earned, not assumed.

#### 9.1.8 Decay and Circle Management

A fact is a fact. Facts do not decay in truth value. "Troy has an MD" does not become less true over time. What changes is whether a fact is in the right circle.

Decay and pruning are therefore **circle management operations**, not information operations:

**Circle 3 maintenance.** Unreconciled facts accumulate. The appropriate response is not auto-pruning (which discards potentially valuable facts) but **surfacing**: periodically summarizing the Circle 3 queue and asking the human to reconcile the high-value items and dismiss the rest. "You have 47 unreviewed observations, mostly about infrastructure changes in March. Here are the 10 most likely to matter." This is triage on the triage -- the agent's pattern recognition applied to its own staging area.

**Circle 2 → removal.** A fact in Circle 2 may become obsolete (you no longer use that tool, the business no longer offers that service). Detection is either human-initiated ("remove the X entry") or agent-proposed during reconciliation ("You mentioned switching from VS Code to Cursor. Should I update the development tools bolus?"). The agent notices; the human confirms.

**Circle 1 → Circle 2.** A fact in Circle 1 may lose its orientation value. A project that was the primary focus six months ago is now archived. The one-liner should reflect the current focus, not the historical one. This is demotion -- the fact is still true and still in Circle 2, but it no longer earns the always-injected position.

**Circle 2 → Circle 1.** A fact in Circle 2 may gain orientation value. A side project becomes the primary focus. A new credential changes the user's professional identity. This is promotion -- and should be flagged as significant because it changes the system prompt.

In all cases, the human is the final authority on circle placement. The agent can propose movements (promotion, demotion, removal), but the human confirms. The permissiveness slider governs how aggressive the agent is in proposing -- not in executing.

#### 9.1.9 Declarative Knowledge Workflow

The following workflow integrates the four-circle model, the bolus architecture, the intake process, the reconciliation model, and the permissiveness slider into a single end-to-end flow.

```
═══════════════════════════════════════════════════════════════
                  DECLARATIVE KNOWLEDGE WORKFLOW
═══════════════════════════════════════════════════════════════

ENTRY POINTS
─────────────────────────────────────────────────────────────

  [A] Human-Initiated         [B] Agent-Detected         [C] System-Observed        [D] Episodic Source
  (dashboard, form,           (conversation extraction,   (integration, webhook,     (Circle 4: transcripts,
   onboarding interview)       background fact detection)  network scan)              interaction logs)
       │                            │                           │                          │
       │                            │                           │                          │
       ▼                            ▼                           ▼                          │
  ┌──────────┐               ┌─────────────┐            ┌──────────────┐                   │
  │  GROUND  │               │  CANDIDATE  │            │  CANDIDATE   │                   │
  │  TRUTH   │               │  FACT       │            │  FACT        │                   │
  │          │               │             │            │              │                   │
  └────┬─────┘               └──────┬──────┘            └──────┬───────┘                   │
       │                            │                          │                           │
       │                            └────────────┬─────────────┘                           │
       │                                         │                                         │
       │                  ┌──────────────────────┐│┌────────────────────────────────────────┘
       │                  │                      │││
       │                  │                      ▼▼▼
       │                  │         ┌────────────────────────┐
       │                  │         │  CIRCLE 3              │
       │                  │         │  Agent's Curation      │
       │                  │         │  Layer                  │
       │                  │         │                        │
       │                  │         │  - candidate fact      │
       │                  │         │  - source citation     │
       │                  │         │  - date detected       │
       │                  │         │  - suggested bolus     │
       │                  │         │  - provenance tag      │
       │                  │         └──────────┬─────────────┘
       │                  │                    │
       │                  │     ┌──────────────┴──────────────┐
       │                  │     │                             │
       │                  │     ▼                             ▼
       │                  │  ┌─────────────────┐   ┌──────────────────┐
       │                  │  │ PERMISSIVE      │   │ RESTRICTIVE      │
       │  (human curation │  │ (slider 4-5)    │   │ (slider 1-3)     │
       │   C4→C2 direct)  │  │                 │   │                  │
       │                  │  │ Low-consequence  │   │ ★ HUMAN          │
       │                  │  │ facts auto-     │   │   RECONCILIATION │
       │                  │  │ promote to      │   │                  │
       │                  │  │ Circle 2.       │   │ Confirm → C2     │
       │                  │  │                 │   │ Reject  → remove │
       │                  │  │ High-consequence│   │ Defer   → stay   │
       │                  │  │ facts still     │   │                  │
       │                  │  │ require human   │   │                  │
       │                  │  │ reconciliation. │   │                  │
       │                  │  └────────┬────────┘   └────────┬─────────┘
       │                  │           │                      │
       │                  │           └──────────┬───────────┘
       │                  │                      │
       │                  │             (confirmed facts only)
       │                  │                      │
       ▼                  ▼                      ▼
═══════════════════════════════════════════════════════════════
              BOLUS ROUTING (applies to all confirmed facts)
═══════════════════════════════════════════════════════════════

  ┌─────────────────────────────────────────────────────────┐
  │  ★ DECISION: WHICH BOLUS? ★                            │
  │                                                         │
  │  Does this fact belong to an existing bolus?            │
  │   YES → route to that bolus in Circle 2                 │
  │   NO  → create new bolus or route to general bolus      │
  └────────────────────────┬────────────────────────────────┘
                           │
                           ▼
  ┌─────────────────────────────────────────────────────────┐
  │  ★ DECISION: DOES THIS CHANGE CIRCLE 1? ★             │
  │                                                         │
  │  Does this fact change how the agent should behave      │
  │  on a TYPICAL interaction?                              │
  │                                                         │
  │   YES → Update Circle 1 (declarative injection file)    │
  │         - Add/update summary line in bolus manifest     │
  │         - Flag as significant change for human review   │
  │                                                         │
  │   NO  → Circle 2 only. Ensure Circle 1 has a pointer   │
  │         to this bolus if none exists yet.               │
  └────────────────────────┬────────────────────────────────┘
                           │
                           ▼
  ┌─────────────────────────────────────────────────────────┐
  │  WRITE-TIME VERIFICATION                                │
  │                                                         │
  │  - Contradiction with existing facts in same bolus?     │
  │    → Resolve by provenance hierarchy (Section 6)        │
  │    → Escalate to human if ambiguous                     │
  │  - Circle 1 still within token budget?                  │
  │  - Pointer from Circle 1 reaches Circle 2 content?     │
  └─────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════
                     RETRIEVAL AT RUNTIME
═══════════════════════════════════════════════════════════════

  Session starts
       │
       ▼
  ┌─────────────────────────────────────────────────────────┐
  │  CIRCLE 1: DECLARATIVE INJECTION                        │
  │  (single file, every session, cached after first turn)  │
  │                                                         │
  │  Contains:                                              │
  │   - Identity, orientation, behavioral constraints       │
  │   - Bolus manifest (summary + pointer per bolus)        │
  │   - Skill manifest (capability + trigger per skill)     │
  │   - Recency context (compiled from Circle 4)            │
  │                                                         │
  │  ONLY CIRCLE 1 IS INJECTED.                             │
  │  CIRCLES 2, 3, AND 4 ARE NEVER INJECTED.                │
  └────────────────────────┬────────────────────────────────┘
                           │
                           ▼
  ┌─────────────────────────────────────────────────────────┐
  │  CIRCLE 2 RETRIEVAL (pull, never push)                  │
  │                                                         │
  │  [1] Agent self-retrieval                               │
  │      Follows categorical pointer from Circle 1.         │
  │      Content enters context as tool result.             │
  │                                                         │
  │  [2] User-directed retrieval                            │
  │      Human explicitly requests detail.                  │
  │                                                         │
  │  [3] System-triggered retrieval                         │
  │      Deterministic pattern match (caller ID, skill      │
  │      trigger, working directory detection).             │
  │                                                         │
  │  Content is ephemeral in the context window.            │
  └────────────────────────┬────────────────────────────────┘
                           │
                           ▼
  ┌─────────────────────────────────────────────────────────┐
  │  CIRCLE 3 RETRIEVAL (pull, with qualification)          │
  │                                                         │
  │  Only at permissiveness 3+. Agent may consult Circle 3  │
  │  when Circle 2 doesn't have the answer. Content is      │
  │  presented with provenance qualification:               │
  │  "Based on a prior conversation, you may have..."       │
  │                                                         │
  │  At permissiveness 1-2, Circle 3 is not consulted       │
  │  during retrieval. It exists only as a reconciliation   │
  │  queue.                                                 │
  └─────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════
                     CIRCLE MANAGEMENT (ongoing)
═══════════════════════════════════════════════════════════════

  ┌─────────────────────────────────────────────────────────┐
  │  INWARD MOVEMENT:                                       │
  │  Circle 4 → Circle 3:  Agent compilation extracts       │
  │                         candidate facts from episodes   │
  │  Circle 4 → Circle 2:  Human curation promotes          │
  │                         directly (bypasses Circle 3)    │
  │  Circle 4 → Circle 1:  Recency context compiled and     │
  │                         refreshed post-session          │
  │  Circle 3 → Circle 2:  Human reconciliation confirms    │
  │  Circle 2 → Circle 1:  Promotion (knowledge gains       │
  │                         orientation value)               │
  │                                                         │
  │  OUTWARD MOVEMENT:                                      │
  │  Circle 1 → Circle 2:  Demotion (knowledge loses        │
  │                         orientation value)               │
  │  Circle 2 → Removed:   Obsolescence (no longer true     │
  │                         or relevant)                     │
  │  Circle 3 → Removed:   Rejected during reconciliation   │
  │  Circle 4 → Archived:  Per retention policy post-       │
  │                         compilation                      │
  │                                                         │
  │  All movements except automated Circle 4 capture:       │
  │  agent proposes, human confirms. Permissiveness         │
  │  slider governs proposal aggressiveness.                │
  └─────────────────────────────────────────────────────────┘
```

**Summary of decision boundaries:**

| Decision | Who Decides | Notes |
|----------|-------------|-------|
| Raw episode captured to Circle 4 | System (automated) | Transcripts, interaction logs land automatically. No human action needed. |
| New fact enters via dashboard/form | Human | Ground truth. Goes directly to Circle 2 (or Circle 1). Bypasses Circles 3 and 4. |
| Agent extracts from Circle 4 | Agent compiles to Circle 3 | Compilation pipeline reads episodes, deposits candidate facts in Circle 3. |
| Human curates from Circle 4 | Human promotes to Circle 2 | Bypasses Circle 3. Human reads episode, promotes directly. |
| Agent detects fact in conversation | Agent extracts to Circle 3 | Permissiveness slider governs auto-promotion vs. reconciliation. |
| System observes state change | System writes to Circle 3 | Same governance as agent-detected. |
| Which bolus? | Human (direct entry) or agent-suggests/human-confirms | Agent may suggest creating a new bolus; human approves. |
| Promote to Circle 1? | Human confirms | Always flagged as significant. Agent proposes; human decides. |
| Resolve contradiction at write time | Provenance hierarchy, escalate if ambiguous | Per Section 6: human-authored supersedes interaction-derived. |
| Retrieve from Circle 2 | Agent, user, or system trigger | Agent uses Circle 1 pointers. No blind search. |
| Retrieve from Circle 3 | Agent (permissiveness 3+) | Always with provenance qualification. |
| Retrieve from Circle 4 | Human-directed or audit | Rare. Raw transcripts for dispute resolution or recompilation. |
| Permissiveness level | Human sets via dashboard | Function of trust in the system and confidence in the model. |
| Circle management (promote, demote, remove) | Agent proposes, human confirms | Permissiveness governs proposal aggressiveness, not execution authority. |
| Circle 4 retention policy | Human configures at deployment | Days, weeks, or indefinite. Process concern, not knowledge decision. |
| Circle 5 pipeline deployment | Human decides which pipelines run | The 80/20 filter. Front-end curation at the source. |
| Circle 5 → Circle 3 | Behavioral compilation pipeline | Extracts candidate patterns from observations. Same reconciliation path as Circle 4 extractions. |
| Circle 5 retention policy | Human configures per pipeline | Independent of Circle 4. Different sources, different retention needs. |

### 9.2 Procedural Knowledge -- "Building Furniture"

Procedural knowledge is knowing how to produce an outcome. Not what is true (declarative), not what happened (episodic), but how to do something. "When a caller asks about scheduling, check availability, offer the next three open slots, and book the one they choose." "When deploying to production, run tests, build the Docker image, push to the registry, and verify the health check." These are reusable approaches for recurring situations -- the bridge between experience and capability.

The software industry has created significant confusion around procedural knowledge by conflating three distinct layers: tools, skills, and capabilities. Untangling these is necessary before the framework can address procedural knowledge clearly.

#### 9.2.1 The Three Layers -- Tools, Skills, Capabilities

**Tools are infrastructure.** A tool is a single callable operation with typed input and output. `gmail_read_message`, `gcal_create_event`, `query_database`, `read_file`. A tool has no judgment. It executes what it's told. It is the saw, the drill, the chisel. A tool is never a skill for the same reason a stethoscope is not a cardiac exam. Having the tool does not confer the knowledge of how or when to use it.

Tools exist at the implementation layer. They should be invisible to the agent's conceptual model. The agent should not know "I have access to `gmail_read_message`, `gmail_create_draft`, `gmail_search_messages`..." any more than a physician thinks "I have a stethoscope skill." The physician has a cardiac exam skill that happens to use a stethoscope. The agent has an email management skill that happens to call Gmail tools.

**Skills are procedural knowledge.** A skill is knowing how to produce a specific outcome using the available tools. "Manage email" is a skill. It includes knowing when to read (checking for urgent messages), when to draft (responding to a lead), when to search (finding a prior conversation), and when to label (organizing for follow-up). The skill is the judgment layer on top of the tools. It is the furniture builder's understanding of when to use the saw vs. the chisel, in what order, with what technique, to produce a specific result.

A skill contains:
- **An outcome definition.** What does this skill produce? A scheduled appointment. A drafted email. A knowledge base query result. The outcome is what a non-technical person would point to and say "the agent can do that."
- **Procedural logic.** Which tools to call, in what sequence, with what conditional branching. This is the recipe. It may be deterministic (a state machine, a subgraph with fixed topology) or it may involve LLM judgment at decision points within the procedure.
- **Trigger conditions.** What situations activate this skill. Keywords, intents, explicit invocation. The pattern that connects a user need to the procedure that fulfills it.

A skill is self-contained. It encapsulates its own tool calls, error handling, and output formatting. The agent doesn't need to know the internal steps. It calls the skill with an intent and gets a result.

**Capabilities are the agent's manifest of skills.** What the agent can do, expressed as a list of human-recognizable outcomes. "This agent can manage email, schedule appointments, and answer questions about company policies." Three lines in the Circle 1 declarative injection. Each capability maps to one skill. The manifest lists capabilities; the skills contain the procedures; the tools are invisible infrastructure inside the skills.

This is the same progressive disclosure pattern as declarative knowledge. Circle 1 has the capability manifest (the agent knows what it can do). The skill's procedural detail loads when activated (the agent knows how to do it). The tools never surface to the agent at all (the implementation is hidden).

#### 9.2.2 The Transport Layer Inversion

The current industry pattern (MCP, function calling) places the transport layer between the agent and each tool:

```
Agent (LLM)
    │
    ├── Transport (MCP) ──→ Gmail Server ──→ gmail_read_message
    │                                    ──→ gmail_create_draft
    │                                    ──→ gmail_search_messages
    │                                    ──→ gmail_list_labels
    │                                    ──→ gmail_send_draft
    │
    ├── Transport (MCP) ──→ Calendar Server ──→ gcal_list_events
    │                                       ──→ gcal_create_event
    │                                       ──→ gcal_find_free_time
    │
    └── Transport (MCP) ──→ Stripe Server ──→ stripe_create_charge
                                           ──→ ...
```

The LLM sees every tool. Twenty, thirty, forty function declarations in the context window, consuming tokens on every turn whether they're used or not. The LLM must reason about which tools to call, in what order, for every request. This is a progressive disclosure failure: the implementation layer is fully exposed to the reasoning layer at all times.

The inverted pattern places the transport layer between the agent and each skill:

```
Agent (LLM)
    │
    ├── Skill: "Manage Email"
    │     └── Transport (auth, retry, rate limits)
    │           ├── gmail_read_message     ← invisible to LLM
    │           ├── gmail_create_draft     ← invisible to LLM
    │           └── gmail_search_messages  ← invisible to LLM
    │
    ├── Skill: "Schedule Appointments"
    │     └── Transport (auth, retry, rate limits)
    │           ├── gcal_find_free_time    ← invisible to LLM
    │           └── gcal_create_event      ← invisible to LLM
    │
    └── Skill: "Process Payments"
          └── Transport (auth, retry, rate limits)
                └── stripe_create_charge   ← invisible to LLM
```

The LLM sees three skill declarations, not twenty tool declarations. The function declarations in the context window are:

```
manage_email(intent: str, details: dict) → result
schedule_appointment(intent: str, details: dict) → result
process_payment(intent: str, details: dict) → result
```

**What this changes:**

*Token budget.* Three function declarations instead of twenty. The savings compound on every turn because function declarations are present in the context window for the duration of the session. For a voice agent where token budget directly affects cost and latency, this is significant.

*LLM reasoning load.* The LLM reasons about what to do (which skill to invoke), not how to do it (which tools to call in what order). The procedural knowledge lives in the skill, not in the LLM's ad-hoc reasoning. This produces more consistent results because the procedure is authored and tested, not re-derived on every request.

*Auth and infrastructure.* Credentials, retry logic, rate limiting, and error handling live at the skill boundary. The skill knows what credentials it needs and manages them for all its internal tool calls. A "Manage Email" skill handles Gmail OAuth for all email operations. A "Schedule Appointments" skill handles Calendar OAuth for all scheduling operations. The agent doesn't know or care about auth.

*Portability.* A skill can be plugged into any agent that has the underlying tool access configured. The skill's interface is stable (intent in, result out). The tool bindings are configured at deployment time per environment. The same "Schedule Appointments" skill works whether the underlying calendar is Google, Outlook, or a proprietary system -- the skill author can abstract the tool layer behind an internal interface.

**MCP's role in the inverted model.** MCP (or any tool protocol) remains useful as the internal transport between skills and external services. The skill needs a standardized way to call Gmail APIs with auth, retries, and error handling. MCP does that well. The mistake is exposing MCP's tool-level granularity to the agent. MCP should be the plumbing inside the walls, not the interface on the wall plate. The skill is the wall plate -- a clean, outcome-oriented interface that hides the plumbing.

**Novel composition does not require tool-level visibility.** A common objection to hiding tools is that the LLM loses the ability to compose tools in novel ways the skill author didn't anticipate. Consider: "Search my email for the invoice from Shane, then create a calendar event with the due date from that invoice, then draft an email to Shane confirming I've scheduled the payment." This crosses email and calendar and seems to require tool-level orchestration. But at the skill level:

```
1. manage_email(intent="find Shane's latest invoice, extract due date and amount")
   → {due_date: "2026-04-30", amount: "$2,400", subject: "Cortivus Q2 Invoice"}

2. schedule_appointment(intent="create payment reminder for April 30, Cortivus invoice $2,400")
   → {event_id: "abc123", scheduled: "2026-04-30 09:00"}

3. manage_email(intent="draft email to Shane confirming payment scheduled for April 30")
   → {draft_id: "xyz789", status: "draft ready for review"}
```

The LLM never needed to know about `gmail_search_messages` or `gcal_create_event`. It decomposed the request into skill-level intents and threaded context between them. The novel composition happened at the skill level. The underlying assumption -- that each skill is broad enough to handle natural language intents within its domain -- is a skill design discipline, not an LLM reasoning burden. Skills that accept intents rather than rigid parameters enable the same compositional flexibility that tool-level visibility provides, without the token cost or reasoning overhead.

#### 9.2.3 The Intent Resolution Layer

Most skill invocations can be handled deterministically. "Schedule an appointment for Tuesday at 3 PM" maps to a clear tool sequence inside the scheduling skill without ambiguity. But some intents require judgment within the skill. "Find Shane's latest invoice and extract the due date" requires the email skill to decide: search by sender? By subject keyword? By date range? What counts as an "invoice"?

When deterministic logic cannot resolve the intent to a tool sequence, the skill needs an internal reasoning step. This is the **intent resolution layer** -- a lightweight LLM call that operates inside the skill boundary with a specific, constrained purpose.

**How it works:**

```
Skill receives intent from agent
       │
       ▼
  ┌─────────────────────────────────────────────┐
  │  DETERMINISTIC RESOLUTION (try first)        │
  │                                              │
  │  Can the intent be mapped to a tool          │
  │  sequence through pattern matching,          │
  │  keyword extraction, or conditional logic?   │
  │                                              │
  │   YES → execute the tool sequence directly   │
  │   NO  → invoke the intent resolution layer   │
  └──────────────────┬──────────────────────────┘
                     │
                (deterministic failed)
                     │
                     ▼
  ┌─────────────────────────────────────────────┐
  │  INTENT RESOLUTION (lightweight LLM call)    │
  │                                              │
  │  A scoped LLM call that receives:           │
  │   - The user's intent (natural language)     │
  │   - THIS SKILL'S tool list only             │
  │   - The skill's procedural instructions      │
  │                                              │
  │  The LLM sees only the 3-5 tools that       │
  │  belong to this skill, not the 40 tools     │
  │  across the entire system. This is           │
  │  progressive disclosure at the skill layer.  │
  │                                              │
  │  The LLM resolves the intent to a specific   │
  │  tool sequence within the skill's scope.     │
  │                                              │
  │  If the intent falls outside the skill's     │
  │  tool coverage:                              │
  │   → REJECT: return to the agent with         │
  │     "this skill cannot fulfill that intent"  │
  │   → The agent-level LLM re-routes or         │
  │     decomposes differently                   │
  └─────────────────────────────────────────────┘
```

**Why this is progressive disclosure, not a workaround:**

The agent-level LLM sees three skills and reasons about what to do. When a skill is invoked, the intent resolution LLM (if needed) sees three to five tools and reasons about how to do it. The total tool surface at any reasoning step is small and relevant. Compare this to the flat MCP model where the LLM sees forty tools at every turn and reasons about both what and how simultaneously.

The progressive disclosure cascade:

| Layer | What the LLM sees | Reasoning task |
|-------|-------------------|----------------|
| Agent level | 3-5 skill declarations (Circle 1 manifest) | Decompose user request into skill-level intents |
| Skill level (deterministic) | Nothing -- no LLM involved | Map intent to tool sequence via procedural logic |
| Skill level (intent resolution) | 3-5 tools belonging to this skill only | Resolve ambiguous intent to tool sequence within the skill's scope |

Each layer has a bounded, relevant context. No layer sees the full system. The LLM is never reasoning about forty tools. At worst, it reasons about five -- and only when deterministic logic can't handle the intent.

**The intent resolution layer is optional per skill.** Simple skills with clear, structured inputs (e.g., "check weather for location X") may never need it. Complex skills with broad intent coverage (e.g., "manage email") will use it for ambiguous or novel requests. The skill author decides whether to include intent resolution based on the complexity of the skill's domain. It is a design choice, not a universal requirement.

**The reject path is critical.** When the intent resolution layer determines that the skill's tools cannot fulfill the intent, it rejects cleanly rather than hallucinating a tool sequence. The agent-level LLM receives the rejection and can re-route: try a different skill, decompose the intent differently, or tell the user the capability doesn't exist. This is how the system handles novel requests gracefully -- not by exposing all tools to the LLM, but by letting each skill honestly report whether it can or cannot handle an intent.

#### 9.2.4 Two Levels of Orchestration

The inverted model with intent resolution creates two distinct orchestration layers, each using the right mechanism for its level:

**Agent-level orchestration (LLM).** The LLM decides *what to do*. "The user wants to reply to Shane's email about the Cortivus timeline and then schedule a follow-up meeting." The LLM determines: invoke "Manage Email" to read and reply, then invoke "Schedule Appointments" to book the follow-up. The LLM provides judgment about content, tone, priority, and sequencing at the skill level.

**Skill-level orchestration (deterministic, with LLM fallback).** The skill decides *how to do it*. "Manage Email" receives the intent "reply to Shane's latest about Cortivus timeline" and resolves it: deterministic logic handles the search-read-draft sequence if the pattern is recognized; intent resolution handles it if the request is ambiguous or novel. Either way, the tool sequence executes internally.

This is the correct division. The agent-level LLM reasons about skill composition and user intent. The skill-level logic (deterministic or intent resolution) handles tool mechanics. Neither layer is overwhelmed. The agent-level LLM doesn't waste capacity on tool selection. The intent resolution LLM (when invoked) doesn't waste capacity on cross-skill reasoning.

Cross-skill sequences (email → calendar → email) are handled at the agent level. The LLM calls one skill, gets a result, reasons about it, calls the next skill. The LLM is still the orchestrator at the capability level. Skills orchestrate at the tool level. The intent resolution layer bridges the gap when deterministic orchestration isn't sufficient.

#### 9.2.4 Granularity -- What Makes a Skill a Skill

The granularity question is: what is the right unit?

The test: **if a non-technical person would say "the agent can do X," then X is the right granularity for a skill.** "Manage email" -- yes. "Parse MIME headers" -- no. "Schedule appointments" -- yes. "Validate RFC 5545 iCalendar format" -- no. "Answer questions about company policies" -- yes. "Execute SQL query against SQLite FTS5 index" -- no.

This is the furniture test. "Build furniture" is a skill. "Use a saw" is not a skill. "Cut a mortise-and-tenon joint" is not a separate skill -- it is an internal procedure within the furniture-building skill. A master builder has internalized it. An apprentice might need it documented as a step in the procedure. But it is never a standalone capability on the manifest.

**There are no sub-skills in the framework.** A skill may have internal procedures, conditional branches, multi-step logic. Those are implementation details -- private methods, not public capabilities. The agent doesn't need to know that "Manage Email" internally has a "search and filter" procedure and a "compose response" procedure. It needs to know "Manage Email."

If a procedure becomes useful across multiple skills -- the way "authenticate with Google" is useful for both email and calendar -- that is a shared utility at the implementation layer. It is the equivalent of a shared library. The agent doesn't know about it. The skill developer uses it. This keeps the manifest clean and the agent's reasoning space small.

**The granularity may differ by agent maturity.** A simple voice agent for a plumber needs "Schedule Appointment" as one skill. A complex operations agent managing multi-resource scheduling across time zones and waitlists might benefit from finer-grained skills ("Check Availability," "Manage Waitlist," "Coordinate Resources"). But even in the complex case, the skills are outcome-oriented, not tool-oriented. The finer granularity reflects the complexity of the domain, not the number of API endpoints.

#### 9.2.5 Procedural Knowledge in the Concentric Circle Model

Procedural knowledge maps to the same four-circle architecture as declarative knowledge, with one critical difference: skills are activated by trigger, not queried by content.

**Circle 1 -- The Capability Manifest.** The declarative injection file includes a skill section listing each skill the agent possesses, with a one-line description and trigger conditions. This is the agent's self-knowledge of what it can do. Token cost: one line per skill. An agent with five skills adds maybe 200-300 tokens to Circle 1.

```
Skills:
  - Manage Email: Read, compose, reply, organize. Triggers: email, message, send, draft, inbox.
  - Schedule Appointments: Check availability, book, reschedule, cancel. Triggers: schedule, appointment, book, available, calendar.
  - Answer Company Questions: Query knowledge base for company policies and FAQs. Triggers: question, policy, how, what, do you.
```

**Circle 2 -- The Skill Definitions.** The full procedural instructions for each skill. Outcome definition, step-by-step procedure, error handling, edge cases. These are never injected -- they load when the skill is activated. The skill's procedural content enters the context as a tool result or internal execution context, not as system prompt injection.

**Circle 3 -- Emergent Procedures.** The agent's curation layer for procedural knowledge. In mature systems, the agent may observe patterns in how it chains skills and propose new composite procedures. "I notice that every Friday, you ask me to check email for invoice reminders and then schedule payment processing. Should I create a routine for that?" This is system-observed procedural knowledge -- the agent proposing a new skill extracted from repeated behavior. It enters Circle 3 as a candidate procedure, awaiting human confirmation before becoming a real skill in Circle 2. The permissiveness slider governs how aggressively the agent proposes new procedures.

**Circle 4 -- The Source Material.** Raw episodic records (transcripts, interaction logs) are the source from which procedural patterns are observed. The compilation pipeline reads Circle 4 episodes, identifies repeated successful approaches, and deposits candidate skills in Circle 3. The episodes themselves are not procedural knowledge -- they are the ore from which procedural knowledge is extracted. This is the same Circle 4 → Circle 3 path that feeds the declarative pipeline, but the extraction targets workflow patterns rather than factual statements.

#### 9.2.6 Isolation from Declarative Knowledge

Skills and boluses are separate knowledge types that should remain isolated in storage, even though they interact at runtime.

**Why isolation matters:**

*Portability.* A "Schedule Appointments" skill can be plugged into any agent regardless of what declarative boluses it has. A "Dental Procedures" bolus can be plugged into any agent regardless of what skills it has. Cross-contamination between the two layers destroys this portability. If the scheduling skill contains hardcoded dental terminology, it can't be reused for a plumber.

*Testability.* Skills can be tested in isolation from declarative knowledge (does the procedure execute correctly?) and declarative knowledge can be tested in isolation from skills (does the agent answer factual questions correctly?). Mixing them makes both harder to validate.

*Versioning.* Skills and boluses evolve on different timelines. A skill's procedure may be refined weekly as edge cases are discovered. A bolus may be static for months. Independent versioning requires independent storage.

**Where they interact at runtime:** The skill may consume declarative knowledge during execution. "Answer Company Questions" calls the `rag-query` tool against a declarative bolus. "Schedule Appointments" checks the business hours from a declarative bolus before offering time slots. But this interaction is at runtime, through the skill's internal tool calls. The skill knows which bolus to consult. The bolus doesn't know which skill is calling it. The dependency is one-directional: skills read boluses, boluses don't reference skills.

#### 9.2.7 Procedural Knowledge Workflow

```
═══════════════════════════════════════════════════════════════
                 PROCEDURAL KNOWLEDGE WORKFLOW
═══════════════════════════════════════════════════════════════

SKILL AUTHORING (how skills enter the system)
─────────────────────────────────────────────────────────────

  [A] Human-Authored                [B] Agent-Observed              [C] Circle 4 Source
  (developer writes skill           (agent detects repeated        (compilation pipeline
   definition: outcome,              pattern in conversation,       reads transcripts,
   procedure, triggers,              proposes new composite         extracts workflow
   tool bindings)                    skill)                         patterns)
       │                                 │                              │
       │                                 │                              │
       ▼                                 └──────────┬───────────────────┘
  ┌──────────────┐                                  │
  │  Circle 2    │                                  ▼
  │  Confirmed   │                        ┌──────────────────┐
  │  skill       │                        │  Circle 3         │
  │              │                        │  Candidate skill  │
  └──────┬───────┘                        │  (awaits human    │
         │                                │   confirmation)   │
         │                                └────────┬──────────┘
         │                                         │
         │                              ★ Human confirms ★
         │                                         │
         ▼                                         ▼
  ┌─────────────────────────────────────────────────┐
  │  SKILL REGISTRATION                              │
  │                                                  │
  │  - Skill added to Circle 2 (full definition)    │
  │  - Capability line added to Circle 1 manifest   │
  │  - Triggers registered for activation            │
  │  - Tool bindings configured per environment      │
  └──────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════

SKILL ACTIVATION (how skills execute at runtime)
─────────────────────────────────────────────────────────────

  User request arrives
       │
       ▼
  ┌─────────────────────────────────────────────────┐
  │  CIRCLE 1: CAPABILITY MANIFEST                   │
  │                                                  │
  │  LLM reads the skill section of the declarative  │
  │  injection. Matches user intent to a skill via   │
  │  trigger keywords or semantic understanding.     │
  │                                                  │
  │  If no skill matches: respond from declarative   │
  │  knowledge only (no procedural activation).      │
  └──────────┬──────────────────────────────────────┘
             │
        (skill matched)
             │
             ▼
  ┌─────────────────────────────────────────────────┐
  │  SKILL INVOCATION                                │
  │                                                  │
  │  LLM calls the skill with an intent and details. │
  │  Example: manage_email(                          │
  │    intent="reply to Shane about Cortivus",       │
  │    details={tone: "professional", urgent: false}) │
  │                                                  │
  │  One function declaration. One call.             │
  └──────────┬──────────────────────────────────────┘
             │
             ▼
  ┌─────────────────────────────────────────────────┐
  │  SKILL EXECUTION (inside the skill boundary)     │
  │                                                  │
  │  The skill orchestrates internally:              │
  │                                                  │
  │  1. Transport layer handles auth, credentials    │
  │  2. Procedural logic determines tool sequence    │
  │  3. Tools execute (invisible to LLM):            │
  │     gmail_search → gmail_read → gmail_draft      │
  │  4. May consult declarative boluses via tools    │
  │  5. May use lightweight LLM call for content     │
  │     generation (draft text, not orchestration)   │
  │  6. Error handling and retry (internal)          │
  │                                                  │
  │  THE LLM DOES NOT SEE THE TOOLS.                 │
  │  THE LLM DOES NOT ORCHESTRATE THE SEQUENCE.      │
  └──────────┬──────────────────────────────────────┘
             │
             ▼
  ┌─────────────────────────────────────────────────┐
  │  RESULT RETURNED TO AGENT                        │
  │                                                  │
  │  Skill returns a structured result:              │
  │   - outcome: "Draft reply composed"              │
  │   - content: (the draft text)                    │
  │   - metadata: (thread_id, timestamp)             │
  │   - needs_confirmation: true/false               │
  │                                                  │
  │  LLM reasons about the result and continues.     │
  │  May invoke another skill (cross-skill chain).   │
  └─────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════

CROSS-SKILL ORCHESTRATION (LLM level)
─────────────────────────────────────────────────────────────

  User: "Reply to Shane about Cortivus and then
         schedule a follow-up meeting next week."
       │
       ▼
  LLM reasons: two skills needed, sequential.
       │
       ├─→ Invoke: manage_email(intent="reply to Shane...")
       │     └─→ Result: draft composed, thread context
       │
       ├─→ LLM uses email context to inform meeting details
       │
       └─→ Invoke: schedule_appointment(intent="follow-up
             with Shane next week, re: Cortivus")
               └─→ Result: meeting booked, confirmation

  The LLM orchestrates BETWEEN skills.
  Skills orchestrate WITHIN their tool calls.
  Two layers. Right mechanism at each level.
```

**Summary of procedural decision boundaries:**

| Decision | Who Decides | Notes |
|----------|-------------|-------|
| Which skills an agent has | Human (manifest configuration) | Skills are assigned at deployment, not discovered at runtime. |
| Which skill to invoke for a request | LLM (reads Circle 1 manifest, matches intent) | The LLM reasons about what to do, not how to do it. |
| Which tools to call within a skill | Skill (deterministic procedure) | The LLM does not see or choose tools. |
| How to sequence cross-skill chains | LLM (reasons about results, invokes next skill) | The LLM orchestrates between skills. |
| New skill proposed from observed patterns | Agent proposes to Circle 3, human confirms | Permissiveness slider governs proposal aggressiveness. |
| Tool-level auth and error handling | Skill (transport layer) | Invisible to the agent. Managed at the skill boundary. |
| Skill granularity | Human (the furniture test) | If a non-technical person would say "the agent can do X," X is a skill. |

### 9.3 Episodic Knowledge -- "The Patient's Chart"

Episodic knowledge is the record of what happened. Time-indexed, narrative, accumulative. "Last Tuesday we spent two hours debugging the Nginx config." "Mrs. Johnson called on April 8th and asked for Dave." "The Q3 planning session produced three action items." Old episodes don't become invalid -- they become history.

The clinical analogy is the patient's chart. The chart contains every visit note, every lab result, every procedure report, ordered by date. The physician doesn't read the entire chart on every visit. They read the problem list (declarative -- Circle 1), check recent labs (targeted episodic retrieval), and dive into the full chart only when a specific clinical question demands it. The chart is the source of truth for what happened. The problem list is the distillation of what matters now.

This analogy reveals the central insight about episodic knowledge: **its primary role is as source material, not as a retrieval target.** The chart exists so that facts can be extracted from it, not so that the physician reads it cover to cover. Episodic knowledge feeds the declarative and procedural pipelines. The episodes are the ore; the declarative facts and procedural skills are the refined metal.

#### 9.3.1 The Relationship to Declarative Knowledge -- The Venn Diagram

Episodic and declarative knowledge overlap, but only at the extraction boundary. The overlap is not in the information itself -- it is in the process that converts one into the other.

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   EPISODIC                    DECLARATIVE                   │
│   (what happened)             (what is true)                │
│                                                             │
│   "Last Tuesday we           "We use PostgreSQL"            │
│    decided to use                                           │
│    PostgreSQL instead              ▲                        │
│    of MongoDB"                     │                        │
│         │                     EXTRACTION                    │
│         │                     PROCESS                       │
│         └────────────────────→─────┘                        │
│                                                             │
│   The episode is the          The fact is the               │
│   source record.              durable output.               │
│   It stays episodic.          It enters the                 │
│                               declarative pipeline.         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The episode "Last Tuesday we decided to use PostgreSQL instead of MongoDB" contains a declarative fact ("We use PostgreSQL") embedded in a narrative. The extraction process separates them. The raw episode lives in Circle 4. The compilation pipeline extracts the fact and deposits it in Circle 3 (agent curation), where it awaits reconciliation to Circle 2. The episode stays in Circle 4 as historical record. They are the same event observed from two knowledge-type perspectives, but they are stored and managed separately.

This separation matters for the same reason it matters in medicine. The visit note (episodic) says "Patient reports chest pain radiating to left arm, EKG shows ST elevation, started heparin drip." The problem list (declarative) says "STEMI, treated, on anticoagulation." Both are true. Both are valuable. But they serve different purposes and are accessed differently. The problem list orients the next physician. The visit note provides detail when someone needs to understand exactly what happened.

The extraction process -- converting episodes into declarative facts and procedural skills -- is the highest-value operation in the episodic pipeline. The nightly wiki compilation in the voice agent PRD is exactly this: transcripts (episodes) are compiled into wiki pages (declarative knowledge). The daily log in Cole's memory-compiler is exactly this: session transcripts (episodes) are compiled into concept articles (declarative knowledge). The pattern is universal. Episodes are the raw material. Compilation produces the durable output.

#### 9.3.2 Episodic Knowledge in the Four-Circle Model

Episodic knowledge is where Circle 4 originates and where the four-circle model most clearly demonstrates its value. The episodic lifecycle is the primary feeder of the entire system.

**Circle 4 -- Raw Episodic Capture (Where Episodes Live)**

This is the home of episodic knowledge. All interactions, transcripts, session records, and call logs land here automatically. Circle 4 is the chart -- every visit note, every lab result, every procedure report, in raw form. Its governance is automated: episodes accumulate without human intervention, and the compilation process reads Circle 4 to produce outputs for the other circles.

Circle 4 is the largest layer by volume and the lowest by per-unit retrieval value. A raw conversation transcript is noisy. Its value is as input to the compilation process, not as a retrieval target. Circle 4 also serves as an audit trail -- the ground truth of what actually happened, before compilation shaped it.

**Circle 3 -- Agent-Curated Episodic Extractions**

The compilation pipeline reads Circle 4 and deposits its outputs here. Candidate declarative facts extracted from episodes. Proposed procedural patterns observed across episodes. Compiled session summaries awaiting confirmation. Circle 3 is the agent's curation layer -- what the agent believes is worth keeping from the episodic record, awaiting human reconciliation.

This is the critical link between the episodic and declarative worlds. The agent reads a transcript (Circle 4), decides "the user mentioned a Google Cloud certificate" (extraction), and deposits that candidate fact in Circle 3. The fact then follows the declarative reconciliation process (9.1.7) toward Circle 2.

**Circle 2 -- Confirmed Compiled Records (Episodic Boluses)**

Compiled episodic content that has been human-confirmed or compiled through a trusted process lives here as episodic boluses alongside declarative and procedural boluses. Session summaries, compiled daily logs, interaction records distilled to their decision-relevant content. Each entry is time-stamped, attributed, and structured for retrieval.

Circle 2 episodic entries have been through a compilation step that shapes them for utility:
- Raw transcripts are summarized to their key exchanges, decisions, and action items
- Redundant turns are collapsed
- Declarative facts have been extracted and routed to declarative boluses (they don't live here in duplicate)
- What remains is the narrative: what was discussed, what was decided, what was left open

Retrieval from Circle 2 is on-demand and typically temporal or associative: "What did we discuss about deployment strategy last month?" "When did we last change the service area boundaries?" The query patterns are time-range filters and keyword search.

Content arrives here through two paths: agent compilation confirmed through reconciliation (Circle 4 → Circle 3 → Circle 2), or direct human curation (Circle 4 → Circle 2, bypassing Circle 3 because the human's judgment is ground truth).

**Circle 1 -- Recency Context (Compiled from Circle 4)**

The episodic component of Circle 1 is not a history. It is a compact orientation to what has been happening recently -- the equivalent of "the patient was admitted three days ago for pneumonia, improving on antibiotics, culture pending." It tells the agent where things stand, not the full story.

Recency context includes:
- What was discussed in the last session or the last few sessions (continuity)
- What is currently in progress (active threads of work)
- What changed recently that the agent should be aware of (recent decisions, unresolved questions)

This is small -- a few hundred tokens at most. It is compiled directly from Circle 4 (recent episodes) as a post-session step: summarize what happened, update the recency block in Circle 1, discard the previous version. There is no separate episodic injection. Circle 1 is one file, one injection, as established in Section 9.1.5.

The recency context is the most perishable component of Circle 1. Yesterday's is stale. Last week's is useless.

| Circle | Episodic Content | Trust | Injected? | Retrieval |
|--------|-----------------|-------|-----------|-----------|
| 1 | Recency context (compiled from Circle 4, refreshed post-session) | Compiled | Yes, as part of the single injection file | Automatic (system prompt) |
| 2 | Compiled episodic boluses (session summaries, daily logs) | Confirmed | Never | On-demand (temporal, associative) |
| 3 | Agent-curated extractions (candidate facts, proposed patterns from episodes) | Provisional | Never | On-demand (with qualification, permissiveness 3+) |
| 4 | Raw episodes (transcripts, interaction logs, session records) | Unprocessed | Never | Rarely (audit, recompilation, direct human curation) |

#### 9.3.3 The Compilation Pipeline

The compilation pipeline is the central process of the episodic system. It reads raw episodes from Circle 4 and produces outputs for the other circles: candidate facts for Circle 3 (awaiting reconciliation), compiled summaries for Circle 2 (via confirmation or direct human curation), and recency context for Circle 1. It is the equivalent of the physician sitting down after a patient encounter and writing the visit note, updating the problem list, and placing orders.

```
═══════════════════════════════════════════════════════════════
                  EPISODIC COMPILATION PIPELINE
═══════════════════════════════════════════════════════════════

  Raw episode lands in Circle 4
  (transcript, interaction log, session record)
       │
       ▼
  ┌─────────────────────────────────────────────────┐
  │  COMPILATION TRIGGER                             │
  │                                                  │
  │  When does compilation fire?                     │
  │   - Post-session (after each session ends)       │
  │   - Scheduled batch (nightly, per the wiki PRD)  │
  │   - Threshold-based (after N new episodes)       │
  │   - Manual (user requests compilation)           │
  │                                                  │
  │  The trigger is a process configuration, not an  │
  │  information decision. Different use cases use   │
  │  different triggers.                             │
  └──────────┬──────────────────────────────────────┘
             │
             ▼
  ┌─────────────────────────────────────────────────┐
  │  EXTRACTION (LLM or deterministic)               │
  │                                                  │
  │  The compiler reads the raw episode and produces │
  │  three outputs:                                  │
  │                                                  │
  │  [1] DECLARATIVE FACTS                           │
  │      Statements about what is true, extracted    │
  │      from the narrative.                         │
  │      → Deposited in Circle 3 (agent curation)   │
  │      → Subject to reconciliation per 9.1.7      │
  │      → Confirmed facts promoted to Circle 2     │
  │                                                  │
  │  [2] EPISODIC SUMMARY                            │
  │      The compiled visit note: what happened,     │
  │      what was decided, what remains open.        │
  │      → Deposited in Circle 3 or Circle 2        │
  │        (depending on permissiveness level)       │
  │      → Time-stamped, structured, retrievable    │
  │                                                  │
  │  [3] RECENCY CONTEXT UPDATE                      │
  │      A refresh of the "where things stand" block │
  │      in Circle 1.                                │
  │      → Overwrites previous recency context      │
  │      → Included in next session's injection     │
  │                                                  │
  │  [4] PROCEDURAL PATTERNS (optional, future)      │
  │      Workflow patterns observed across episodes. │
  │      → Deposited in Circle 3 (agent curation)   │
  │      → Subject to human confirmation per 9.2    │
  └──────────┬──────────────────────────────────────┘
             │
             ▼
  ┌─────────────────────────────────────────────────┐
  │  STATE TRACKING                                  │
  │                                                  │
  │  - Mark Circle 4 episode as compiled (hash)       │
  │  - Record compilation metadata (date, cost,      │
  │    number of facts extracted, summary length)    │
  │  - Circle 4 raw episode retained for audit       │
  │    or pruned per retention policy                │
  └─────────────────────────────────────────────────┘
```

**The compilation step is where episodic knowledge creates value for the other knowledge types.** Without compilation, episodes are an ever-growing archive that nobody reads. With compilation, each episode feeds the declarative knowledge base (new facts discovered), the procedural knowledge base (new patterns observed), and the recency context (the agent stays current). The episode itself, once compiled, is primarily archival.

This is why the earlier discussion of the learned knowledge wiki and Cole's memory-compiler converged on the same architecture. Both are compilation pipelines that convert episodes (conversations, transcripts) into declarative knowledge (wiki pages, concept articles). The framework generalizes this: episodic knowledge's primary value is realized through compilation into other knowledge types.

#### 9.3.4 When Episodic Knowledge Is Retrieved Directly

Compilation handles the common case. But there are situations where an episode is the target, not the source:

**Temporal recall.** "What did we discuss about Cortivus last month?" The user wants the narrative, not a fact extracted from it. The answer comes from Circle 2 (compiled session summaries) via time-range filter and keyword search. The Circle 1 recency context doesn't help here because it only covers the recent past.

**Context reconstruction.** "Why did we decide to use PostgreSQL?" The declarative fact ("we use PostgreSQL") is in the declarative bolus. But the reasoning behind it is episodic -- it lives in the session summary from the day the decision was made. The agent follows the declarative fact's source attribution (which links back to the episode) to retrieve the narrative context.

**Audit and dispute resolution.** "What exactly did I say about the service area boundaries?" The compiled summary may have lost nuance. The raw transcript in Circle 4 is the ground truth. This is the exception case -- most retrieval targets Circle 2, but Circle 4 exists for when the compiled version isn't sufficient.

**Pattern recognition across time.** "Have we had this problem before?" The agent searches Circle 2 for prior episodes involving similar issues. This is associative retrieval across the temporal dimension -- the one scenario where vector search against episodic records may be justified, because the user doesn't know the exact terms or dates.

In all these cases, episodic retrieval is on-demand (never injected) and uses the retrieval mechanisms matched to the query pattern per Section 2 (Q7): temporal queries use time-range filters, associative queries use keyword or semantic search, audit queries go to Circle 4 raw records.

#### 9.3.5 What Episodic Knowledge Is Not

**Episodic knowledge is not conversation history.** The current session's conversation is session-dynamic working memory -- it lives in the context window and is managed by the LLM runtime (compaction, summarization). It is not episodic knowledge until the session ends and the transcript becomes a raw episode in Circle 4. The framework draws a hard line between the active conversation (runtime concern) and the historical record (episodic knowledge).

**Episodic knowledge is not a declarative knowledge store.** When someone says "the agent should remember that I prefer PostgreSQL," they want a declarative fact, not an episode. The fact that this preference was stated in Tuesday's session is episodic. The preference itself is declarative. Systems that store "user prefers PostgreSQL" as an episode (timestamped, narrative) instead of a fact (structured, categorical) are misclassifying the knowledge type and will pay for it in retrieval quality. The compilation pipeline exists precisely to prevent this: extract the fact, route it to declarative, leave the episode as narrative.

**Episodic knowledge is not a substitute for compilation.** Storing every transcript and searching them on demand (the RAG-over-conversations approach) is an anti-pattern. It treats episodic knowledge as the retrieval target when it should be the compilation source. A well-compiled declarative knowledge base with source attribution back to episodes is strictly more useful than a searchable archive of raw transcripts. The compiled output is structured, deduplicated, and shaped for retrieval. The raw transcript is noisy, redundant, and shaped for nothing.

#### 9.3.6 The Retention Question

Episodic knowledge grows linearly with usage. Every session, every call, every interaction produces an episode. Without a retention policy, Circle 4 grows without bound.

The retention question is not about truth (episodes don't become false) but about utility and cost:

**Circle 4 (raw episodes):** Highest volume, lowest per-unit value after compilation. Retention policy options:
- Retain indefinitely (audit-heavy domains, cheap storage)
- Retain for N days post-compilation, then archive or delete (most use cases)
- Retain only episodes that produced flagged or disputed facts (selective audit trail)

**Circle 3 (agent-curated extractions):** Unreconciled candidates from Circle 4. Same maintenance as described in 9.1.8 -- periodic surfacing and reconciliation, not auto-pruning.

**Circle 2 (compiled records):** Moderate volume, durable value. Session summaries and compiled logs are the permanent historical record. Retention is typically indefinite, but older entries can be compacted further over time -- monthly summaries compiled from daily summaries, quarterly summaries from monthly. This is progressive summarization: each compaction layer distills the prior layer, and the full detail is available one layer down if needed.

**Circle 1 (recency context):** Smallest volume, highest perishability. Overwritten after every session. No retention question -- there is only the current version.

The retention policy is a process configuration, not a knowledge architecture decision. Different use cases set different retention windows. A personal assistant might retain raw transcripts for 30 days. A voice agent for a business might retain them for 90 days (regulatory reasons) or 7 days (cost reasons). The framework doesn't prescribe a window -- it prescribes that the question be answered explicitly at deployment time.

#### 9.3.7 Episodic Knowledge Workflow Summary

| Aspect | Episodic Approach |
|--------|------------------|
| Primary role | Source material for compilation into declarative facts and procedural skills |
| Circle 4 content | Raw episodes -- transcripts, interaction logs, unprocessed source material |
| Circle 3 content | Agent-curated extractions from episodes -- candidate facts, proposed patterns, compiled summaries awaiting confirmation |
| Circle 2 content | Confirmed compiled records -- session summaries, daily logs, structured for retrieval (as episodic boluses) |
| Circle 1 content | Recency context -- compiled summary of recent sessions, refreshed post-session |
| Injection | Recency context only, as part of the single injection file. No separate episodic injection. |
| Primary process | Compilation pipeline: Circle 4 (raw episode) → Circle 3 (agent-curated extractions) → Circle 2 (confirmed via reconciliation) + Circle 1 (recency context refresh) |
| Direct retrieval | On-demand only. Temporal (time-range filter against Circle 2), associative (keyword/semantic search against Circle 2), or audit (Circle 4 raw) |
| Overlap with declarative | At the extraction boundary. Circle 4 episodes contain facts. Compilation extracts them into Circle 3. Reconciliation promotes them to Circle 2 declarative boluses. The episode stays in Circle 4. The fact becomes declarative in Circle 2. |
| Overlap with procedural | At the pattern observation boundary. Repeated successful approaches observed across Circle 4 episodes become candidate skills in Circle 3. Human confirmation promotes them to Circle 2 skill definitions. |
| Retention | Circle 4 has a configurable retention window. Circle 3 follows reconciliation maintenance (9.1.8). Circle 2 is retained indefinitely with progressive summarization. Circle 1 is overwritten per session. |
| Human role | Review compilation output (via Circle 3 reconciliation). Curate directly from Circle 4 to Circle 2 when desired. Set retention policy. Direct episodic recall on demand. |

---

## 10. Critique and Open Risks

This section identifies the areas where the framework's logic is sound but its survival in production is uncertain. These are not theoretical objections -- they are the specific failure modes most likely to degrade the system from its designed intent. Acknowledging them before implementation is the difference between a framework that learns from its first deployment and one that is abandoned after it.

### 10.1 Reconciliation Fatigue -- The Problem List Problem

The medication reconciliation model is the right analogy and the right architecture. It is also a process that fails routinely in clinical practice, for reasons that translate directly to knowledge systems.

In hospitals, medication reconciliation is a Joint Commission requirement. Every patient, every transition of care. The evidence for its value is unambiguous: accurate medication lists reduce adverse drug events, prevent duplicate therapies, and catch dangerous interactions. And yet clinicians skim it, skip it, and rubber-stamp it -- not because they're careless, but because the volume of reconciliation events outpaces the cognitive budget they have available. A hospitalist with twenty patients, each with fifteen medications, faces three hundred reconciliation decisions per shift. The first five are careful. The next fifty are glanced at. The rest are auto-confirmed.

The same failure mode threatens Circle 3 reconciliation. A system that extracts ten candidate facts per day produces seventy per week. The first week, the human reviews carefully. By month two, the queue has two hundred unreviewed items and the human starts bulk-confirming. By month six, the permissiveness slider has been set to 5 not because trust was earned, but because the human stopped looking.

**This is not a design flaw -- it is a human behavior fact that the design must accommodate.**

Mitigation strategies the implementation should consider:

**Prioritized surfacing over exhaustive review.** Don't present the full Circle 3 queue. Present the top 5-10 items ranked by consequence, novelty, or contradiction potential. "You have 47 unreviewed observations. Here are the 5 most likely to matter." The human reviews the high-signal items; the rest stay in Circle 3 at their current trust level. This is clinical triage applied to reconciliation itself.

**Ambient reconciliation over scheduled review.** Instead of a dedicated reconciliation session (which feels like homework), surface one or two candidate facts naturally during conversation. "By the way, last session you mentioned getting a Google Cloud certificate. Should I add that to your credentials?" This distributes the reconciliation burden across interactions rather than concentrating it into a review session the human will skip.

**Consequence-aware auto-resolution.** Not all facts are equal. "User's preferred IDE is VS Code" has negligible consequences if wrong. "User has an MD credential" has significant consequences if wrong. The system should auto-resolve low-consequence facts at lower permissiveness levels than high-consequence facts. This isn't the permissiveness slider (which is a global setting) -- it's a per-fact consequence assessment that modulates the default behavior within a given permissiveness level.

**Reconciliation metrics.** Track review rates. If the human hasn't reviewed Circle 3 in 30 days, that's a system health signal, not a user choice. Surface it: "Your observation queue hasn't been reviewed in 4 weeks. Would you like a summary of the 10 highest-priority items?" This is the clinical informatics approach -- measure compliance with the process and intervene when it drops.

The honest acknowledgment: some percentage of Circle 3 content will never be reviewed, regardless of interface design. The system must be robust to this. Circle 3 content that is never reconciled should not silently become trusted knowledge. It stays provisional. The provenance qualification ("Based on a prior conversation, you may have...") is the safety net. The system degrades gracefully from "all facts reviewed" to "unreviewed facts are used with lower confidence" rather than from "all facts reviewed" to "unreviewed facts are silently treated as confirmed."

### 10.2 Extraction Quality at Scale

The compilation pipeline (Circle 4 → Circle 3) depends on the LLM correctly identifying which parts of a raw episode are worth extracting and correctly categorizing what it extracts. This is the step where quality failures compound.

**Known extraction failure modes:**

*Sarcasm and hypotheticals stored as facts.* "Yeah, I'm definitely going to rewrite the entire backend in Rust this weekend" is sarcasm. "We could move to PostgreSQL if the performance issues continue" is a hypothetical. Both contain patterns that a naive extractor will store as declarative facts. The extraction prompt must explicitly instruct the LLM to distinguish between statements of fact, hypotheticals, sarcasm, and aspirations. Few-shot examples of each are essential.

*Correction chains lost.* "We use MongoDB... actually wait, we switched to PostgreSQL last month." If the extractor processes statements sequentially without tracking corrections within the same conversation, it may extract both "we use MongoDB" and "we switched to PostgreSQL" as candidate facts. The extraction prompt must instruct the LLM to process the entire episode holistically and extract only the final state after all corrections.

*Context-dependent facts extracted as universal.* "For this project, we're using TypeScript" becomes "we use TypeScript" without the project scoping. The extraction prompt needs to preserve scope qualifiers -- which bolus, which context, which tenant.

*Signal dilution at volume.* A one-hour conversation has maybe 3-5 durable facts in it. The rest is working through problems, discussing options, debugging, and small talk. An extractor that is too aggressive produces a Circle 3 full of low-value observations that bury the high-value facts. An extractor that is too conservative misses facts that the human would have wanted captured.

**The quality measurement gap.** The framework describes configurable extraction prompts per tenant (Section 6) and the reconciliation process as a quality gate. What it doesn't describe is how to measure extraction quality over time. Implementation should track:

- Confirmation rate: what percentage of Circle 3 items are confirmed vs. rejected? A high rejection rate signals the extractor is too aggressive or inaccurate.
- Miss rate: are facts appearing in Circle 2 (via direct human curation from Circle 4) that the extractor should have caught? This is harder to measure but more important -- silent misses are invisible without explicit tracking.
- Contradiction rate: how often do extracted facts contradict existing Circle 2 content? Some contradictions are genuine updates. A high rate may signal the extractor is misinterpreting context.

These metrics should feed back into extraction prompt refinement. The extraction prompt is a configurable artifact (Section 6), but it needs a quality signal to inform iteration. Without measurement, the prompt is tuned by intuition and never improved.

### 10.3 Circle 1 Curation Pressure

The framework states that Circle 1 is constant-sized. This is true by definition -- it's a fixed token budget. But the management burden of keeping it constant-sized grows with system complexity.

An agent with 5 boluses and 3 skills has a simple Circle 1: five summary lines, three capability lines, a recency block, and identity/behavioral constraints. Easy to maintain. Easy to read. Easy to verify.

An agent with 30 boluses and 15 skills approaches the token budget. Now the question becomes: which boluses earn a summary line? Which skills are listed? What level of detail does each entry get? Can some boluses be grouped? Should the skill manifest be abbreviated?

This is the meta-curation problem. The framework has processes for moving knowledge between circles (intake, reconciliation, promotion, demotion). It does not have an explicit process for managing the composition of Circle 1 itself when the manifest grows. This is a gap.

**The problem is real but not immediate.** Most deployments will have 5-15 boluses and 3-10 skills. The pressure becomes acute only when the system scales beyond ~20 boluses, at which point the manifest section alone consumes 2,000-4,000 tokens. For the current target use cases (Atlas, the-agency voice agents, Selah), this threshold is unlikely to be hit soon. But the framework should name the threshold and describe what happens when it's reached -- likely a categorization layer that groups boluses by domain with summary lines per category rather than per bolus.

### 10.4 Scope of Applicability

The framework is designed for and excels at a specific scale: solo operators, small businesses, purpose-built agents with bounded knowledge domains. At this scale, its simplifications are strengths -- wholesale injection over RAG, deterministic retrieval over vector search, human curation over automated extraction.

These simplifications become constraints at enterprise scale. A hospital system with 50,000 policy documents cannot wholesale-inject anything. A law firm with a million case records needs retrieval infrastructure that this framework explicitly argues against at smaller scales. A platform serving 100,000 tenants cannot rely on human reconciliation for quality assurance.

This is not a weakness -- it is scope. The framework's own anti-pattern list (Section 5) includes the Universal Architecture Fallacy: using the same memory architecture for all use cases. The framework should not violate its own principle by claiming universal applicability. It is better than existing approaches *for the use cases it targets*. The triage questions in Section 2 correctly identify when a system has grown beyond the framework's design envelope (large volume, enterprise consumer scope, high-consequence domains with regulatory audit requirements).

The framework is also better than existing approaches at one thing regardless of scale: the conceptual model. The four-circle trust gradient, the distinction between information and process, the single injection point -- these are valid organizing principles even in systems that need more sophisticated retrieval infrastructure. A hospital system still benefits from separating confirmed knowledge from provisional agent observations. It just needs more machinery around each circle than the framework currently describes.

### 10.5 Validation Path

The framework is currently an architectural design. It has not been validated through implementation. The ideas are logically consistent and grounded in clinical informatics analogies, but clinical analogies have a track record of not surviving contact with software reality unchanged.

The highest-confidence elements are those grounded in existing implementations: the single injection file (CLAUDE.md works today), the bolus model (knowledge ingestion works today in Atlas and the-agency), and the compilation pipeline (the wiki PRD describes a buildable system).

The lowest-confidence elements are those that are pure architectural reasoning without implementation precedent: the permissiveness slider (will the five levels be meaningful in practice or collapse to "off" and "on"?), the intent resolution layer (will the scoped LLM call within the skill boundary produce reliable tool sequences?), and Circle 3 as a distinct operational layer (will the distinction between Circle 3 and Circle 4 be maintained in practice, or will they blur into "stuff the agent noticed that I haven't looked at"?).

The recommended validation sequence is:

1. **Build Circle 1 and Circle 2 first.** These are the layers with existing implementation precedent and the most immediate value. A single injection file with a bolus manifest and on-demand retrieval from confirmed boluses. This is Atlas and the-agency today, formalized.

2. **Add Circle 4 capture second.** Transcript logging and raw episode storage. This is already happening in the-agency (transcripts saved to `data/transcripts/`). No new architecture needed -- just formalize it as Circle 4.

3. **Build the compilation pipeline third.** Circle 4 → Circle 3 extraction. This is the learned knowledge wiki, the memory-compiler. Validate extraction quality on real transcripts before trusting it at scale.

4. **Add Circle 3 reconciliation fourth.** The medication reconciliation interface. Build the lightweight UI, measure review rates, iterate on surfacing strategy. This is where the framework's human-behavior assumptions get tested.

5. **Add the permissiveness slider last.** Only after reconciliation has been operational long enough to generate data on review rates and extraction quality. The slider settings should be calibrated from observed behavior, not guessed at from first principles.

6. **Validate the transport layer inversion and intent resolution layer in the-agency's skill architecture.** Build one skill with the inverted model (intent in, result out, tools hidden), measure token savings and result quality against the current MCP-exposed model. If the inverted model produces equivalent or better results at lower token cost, migrate the remaining skills.

This sequence builds confidence incrementally. Each step validates the assumptions that the next step depends on. The framework is built from the center (Circle 1) outward (Circle 4), which mirrors the trust gradient and ensures the highest-value layers are working before the more speculative layers are added.
