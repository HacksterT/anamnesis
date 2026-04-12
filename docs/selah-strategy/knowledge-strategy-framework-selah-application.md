# Knowledge Strategy Framework -- Selah Application & Mem0 Comparative Analysis

**Date:** 2026-04-08
**Companion to:** `knowledge-strategy-frameworkv3.md`
**Purpose:** Apply the Knowledge Strategy Framework to Selah (pastoral AI assistant), map it against Mem0/LightRAG capabilities, and identify the architectural approach for Selah's memory system.

---

## 1. Selah Triage Profile

Running Selah through the framework's ten triage questions:

| Question | Selah Answer |
|----------|-------------|
| Q1. Kind | All three. Declarative (doctrinal positions, congregant preferences, denominational distinctives -- including entity-linking: congregant-to-pastor, family-to-congregation, counseling-case-to-elder-board). Episodic (counseling history, sermon series progression, pastoral session notes). Procedural (pastoral care protocols, counseling frameworks, sermon preparation workflows). |
| Q2. Volume | Small per church (partnership phase: 1-2 pastors, bounded denominational corpus). Medium per church at scale (growing episodic from pastoral sessions). Entity-linking declarative could grow as congregation data accumulates. |
| Q3. Dynamism | Static (bolus: denominational theology, confessional documents). Interaction-dynamic (pastoral memory: learned from sessions, congregant preferences). Session-dynamic (active counseling conversation state). |
| Q4. Provenance | Human-authored (pastor's stated doctrinal positions, denominational confessions -- HIGHEST trust, non-negotiable). Interaction-derived (pastoral case notes extracted from conversations -- medium trust, reviewable). Agent-synthesized (Selah's doctrinal inferences from conversation -- LOWEST trust, must NEVER override pastor's stated position). |
| Q5. Temporal | Historical for pastoral care (old counseling sessions remain valuable -- a congregant's journey over months/years matters). Current-state for doctrinal positions (latest stated view supersedes). Cumulative for sermon preparation (themes build on each other across a series). |
| Q6. Consumer | Single agent per church (MVP). Multi-agent same tenant is future (pastoral team sharing a Selah instance -- associate pastor, youth pastor, senior pastor with different access scopes). |
| Q7. Query | Associative ("what did we discuss about the Thompson family?"). Temporal ("counseling sessions from last quarter"). Categorical ("what's our position on infant baptism?"). Entity-linking traversal ("who in the congregation is connected to this situation?"). |
| Q8. Latency | Interactive (chat interface via Open WebUI, not voice). Tolerant of 1-2 seconds for retrieval. Batch for nightly compilation of session notes. |
| Q9. Consequence | **HIGH for doctrinal.** Wrong doctrinal answer = theological harm. **MEDIUM for pastoral.** Wrong recall = broken pastoral trust. This is closer to the framework's Profile D (enterprise/hospital) than Profile A (personal assistant). Source attribution mandatory. Human-in-the-loop for doctrinal claims. |
| Q10. Growth | Bounded for theology (denominational corpus stabilizes). Linear for pastoral episodes (more sessions = more history). Bounded for procedures (pastoral care workflows are mature, not emergent). |

---

## 2. Framework vs. Mem0 -- Direct Comparison

### Where the Framework Already Covers What Mem0 Does

| Mem0 Feature | Framework Equivalent | Assessment |
|-------------|---------------------|------------|
| ADD/UPDATE/DELETE/NOOP curation | Q4 Provenance + Q3 Dynamism define the curation triggers and trust hierarchy | Framework defines the decision space. Mem0 automates the execution. |
| Vector + Graph + Key-Value hybrid stores | Q7 Query Pattern defines five retrieval patterns (categorical, associative, temporal, exhaustive, pattern-matching) and matches each to the right mechanism | Framework explains WHY you'd pick each store. Mem0 provides the engines. |
| Entity relationship extraction | Q1 Knowledge Kind explicitly defines entity-linking as a subtype of declarative knowledge with traversal-based retrieval | Framework classifies when entity-linking matters. Mem0 does the extraction. |
| Memory decay / forgetting | Q5 Temporal Relevance + Q9 Consequence define when forgetting is safe (current-state declarative) and when it's not (historical episodic) | Framework provides the rules. Mem0 applies a generic algorithm that doesn't distinguish these cases. |
| Cross-session recall | Q5 Historical + Q7 Temporal + Associative retrieval patterns | Framework defines the query patterns. Mem0 provides the infrastructure. |

### Where the Framework Goes Beyond Mem0

**Provenance hierarchy.** Q4 defines four trust levels. Mem0 has no concept of provenance. Everything it stores has the same trust weight. For Selah: a pastor's stated doctrinal position (human-authored) must NEVER be overwritten by Selah's inference (agent-synthesized). Mem0 would treat both equally without custom intervention.

**Injection strategy as a first-class concern.** Mem0 handles ingestion and retrieval. It returns memories. What happens in the context window is your problem. The framework's injection dimension (timing, placement, shaping, token budget, priority) is where most quality gain actually lives. The "shape before injecting" principle alone is worth more than any retrieval improvement.

**The volume branch point.** Below ~5,000 tokens, skip retrieval entirely and inject everything. Most Selah deployments (partnership phase, single pastor, bounded denominational knowledge) will live below this threshold. Mem0 adds retrieval infrastructure that may not be needed at this scale.

**Anti-patterns as guard rails.** The Vector-Everything Fallacy, the Deep Hierarchy Fallacy, the Retrieval-Over-Compilation Fallacy -- these aren't observations, they're architectural constraints. Mem0's default approach (vector everything, retrieve everything) would violate three of the framework's five anti-patterns.

**Consequence-driven architecture.** Q9 drives fundamentally different designs. A productivity tool (Q9=Low) can auto-inject without review. Selah (Q9=High for doctrinal) requires HITL confirmation before agent-synthesized knowledge enters the authoritative store, source attribution mandatory at injection, and audit trail for all changes. Mem0 has no consequence-awareness.

### Where Mem0 Adds Something the Framework Doesn't Address

**Automated curation execution.** The framework defines when and how curation should happen (Q3 + Q4), but Atlas implements this manually (checkpoint, memory file rewrites). Mem0 automates the ADD/UPDATE/DELETE decision per interaction. For Selah, Mem0 would serve as the execution engine for curation rules the framework defines.

**Graph traversal at query time.** The framework identifies entity-linking retrieval as "traversal-based" but Atlas doesn't implement graph traversal. It uses FTS5 + vector. Mem0's Neo4j/Kuzu backend provides actual graph traversal: "given Mrs. Thompson, what counseling sessions, what pastor involvement, what elder board decisions connect to her?" The framework correctly identified this as the right retrieval pattern. Mem0 provides the engine.

---

## 3. Mem0 vs. LightRAG for Selah

| Dimension | Mem0 | LightRAG |
|-----------|------|----------|
| What it is | Memory layer (you plug into things) | Complete RAG system with graph |
| Graph extraction | Mem0 extracts entities, separate DB stores | Built-in (LLM does it during indexing) |
| Graph backends | Neo4j, Kuzu, Apache AGE, Memgraph | Neo4j, PostgreSQL, MongoDB, OpenSearch |
| Ollama support | Yes (explicit config) | Yes (OpenAI-compatible API) |
| Minimum LLM | Any instruction-following model | 32B+ recommended, 64K context |
| Self-hosted | Yes, full Docker support | Yes, full Docker support |
| Resource overhead | Lighter (simpler extraction) | Heavy (extraction requires large LLM) |
| Postgres reuse | pgvector for vectors | PostgreSQL for graph (no Neo4j needed) |

**LightRAG advantage for Selah:** Can use PostgreSQL as graph backend. We already have Postgres 18 + pgvector on port 5432 via search-sophia. No Neo4j Docker container needed -- saves ~512MB-1GB RAM (significant given current swap pressure at 6.5GB).

**LightRAG risk for Selah:** Recommends 32B+ model with 64K context. Gemma 4 26B-A4B is technically under threshold (26B total, 3.8B active as MoE). Extraction quality may degrade. Must test before committing.

**Recommendation:** Test LightRAG with Gemma 4 first (uses Postgres, no Neo4j overhead). If extraction quality is insufficient, fall back to Mem0 + Neo4j (proven path).

---

## 4. Open WebUI Memory vs. Mem0 vs. Framework-Driven Approach

| Capability | Open WebUI Native | Mem0 | Framework-Driven |
|-----------|-------------------|------|-----------------|
| Memory storage | Basic key-value | Hybrid: vector + graph + key-value | Determined by Q1-Q2 triage per knowledge kind |
| Active curation | Minimal | Automated ADD/UPDATE/DELETE/NOOP | Rules defined by Q3+Q4, execution automated or manual |
| Graph relationships | No | Yes | Yes, when Q1 identifies entity-linking + Q7 identifies traversal |
| Provenance hierarchy | No | No | Yes -- four trust levels, conflict resolution rules |
| Injection strategy | Fixed (include all memories) | Returns memories, injection is your problem | First-class: timing, placement, shaping, token budget, priority |
| Consequence awareness | No | No | Yes -- Q9 drives HITL requirements, source attribution |
| Cross-session recall | Basic (recency) | Semantic + relationship-aware | Matched to Q7 query pattern (associative, temporal, categorical) |
| Portability | Locked in Open WebUI DB | Exportable, API-accessible | Portable by design (framework principle) |

**Conclusion:** Open WebUI memory is a convenience feature. Mem0 is infrastructure. The framework governs both -- it defines what memory should DO, while Mem0/LightRAG provide engines for execution.

---

## 5. Recommended Architecture for Selah

Use Mem0 (or LightRAG) as **infrastructure** governed by **the framework**.

### Tier Mapping

| Tier | Selah Component | Storage | Framework Alignment |
|------|----------------|---------|-------------------|
| Tier 1: Identity | System prompt + Ollama Modelfile | Always in context | Q2=Small, Q3=Static, Q4=Human-authored. Wholesale injection. |
| Tier 1.5: Denominational Knowledge | Bolus RAG databases per denomination | SQLite per tradition (physically isolated) | Q1=Declarative, Q2=Small-Medium, Q3=Static, Q4=Human-authored. Pre-session injection, deterministic retrieval. |
| Tier 2: Pastoral Memory | Mem0 conversation memory with custom pastoral extraction prompt | Vector + Key-Value via Mem0 | Q1=Declarative+Episodic, Q3=Interaction-dynamic, Q4=Interaction-derived (medium trust). Provenance-tagged. |
| Tier 3: Relationship Graph | Mem0 graph memory (or LightRAG with Postgres) | Neo4j/Kuzu/Postgres graph | Q1=Declarative (entity-linking subtype), Q7=Traversal. "Given this congregant, what connects?" |
| Tier 4: Session State | LangGraph checkpointer / Open WebUI conversation | SQLite or in-memory | Q3=Session-dynamic. Ephemeral unless promoted by trigger. |
| Skills | Pastoral care protocols, counseling frameworks | YAML skill files or system prompt sections | Q1=Procedural, Q3=Static, Q4=Human-authored. Pattern-match retrieval. |

### Custom Extraction Prompt (Critical)

Mem0's default extraction treats all content equally. For Selah, the extraction prompt must enforce:

1. **Provenance tagging.** Every extracted memory gets a provenance level:
   - `pastor-stated` -- the pastor explicitly said this (highest trust)
   - `session-derived` -- extracted from conversation context (medium trust)
   - `selah-inferred` -- Selah's reasoning or synthesis (lowest trust, flagged for review)

2. **Entity types tuned for pastoral context:**
   - People: congregants, pastors, families, staff
   - Relationships: family, congregation-membership, counseling-relationship, mentoring
   - Events: counseling sessions, sermons, elder meetings, life events (births, deaths, crises)
   - Doctrinal positions: explicit theological stances stated by the pastor
   - Scripture references: passages discussed, interpreted, applied

3. **Exclusion rules:**
   - Do NOT extract casual/social conversation as pastoral memory
   - Do NOT store identifying details of minors without explicit pastoral direction
   - Do NOT override `pastor-stated` provenance with `selah-inferred` -- ever

### Injection Strategy

Following the framework's injection principles:

| Context | Injection Approach | Token Budget |
|---------|-------------------|-------------|
| System prompt (identity + denominational core) | Pre-session wholesale | ~2,000 tokens |
| Relevant pastoral memories (Mem0 retrieval) | On-demand per message | ~1,500 tokens |
| Relationship context (graph traversal) | On-demand when entities are mentioned | ~500 tokens |
| Sermon series continuity | On-demand when sermon prep is detected | ~1,000 tokens |
| Skill definitions | On trigger match | ~500 tokens |

**Total budget:** ~5,500 tokens for grounding context, leaving ample room for conversation and reasoning in the context window.

**Shaping rule:** Raw pastoral session transcripts are NEVER injected. They are compiled into structured summaries at extraction time. The framework's "shape before injecting" principle is load-bearing here -- a 5,000-token counseling transcript should become a 300-token structured summary (date, participants, key topics, decisions, follow-ups).

---

## 6. Implementation Path

### Phase 1: Partnership (Now)

- Open WebUI as chat interface (it works, pastors can use it today)
- Ollama serving Gemma 4 (Q4_K_M for dev, fine-tuned model when ready)
- Denominational bolus via existing RAG pipeline
- No Mem0 yet -- Open WebUI's basic memory is sufficient for 1-2 pastors

### Phase 2: Memory Integration

- Test LightRAG with Gemma 4 + Postgres (no Neo4j overhead)
- If extraction quality insufficient: deploy Mem0 with Kuzu (embedded graph) or Neo4j Docker
- Custom extraction prompt with pastoral provenance rules
- Mem0 runs alongside Open WebUI, not inside it

### Phase 3: Custom Frontend

- Replace Open WebUI with Selah-specific Next.js frontend
- Direct integration with Mem0 API for memory-aware conversations
- Relationship graph visualization for pastoral context
- Full control over injection strategy and token budget management

### Phase 4: Production

- RunPod Serverless for inference (fine-tuned BF16)
- Postgres for production state and graph (if using LightRAG/Apache AGE)
- Multi-tenant: per-church isolation (separate Mem0 instances or user_id scoping)
- Provenance-aware dashboard for pastors to review and correct Selah's memories

---

## 7. Key Insight

**The framework is the brain. Mem0/LightRAG are the hands.**

Mem0 automates memory operations. LightRAG automates graph construction. Neither understands the domain. The Knowledge Strategy Framework provides the decision logic that governs when to store, what to trust, how to retrieve, and what to inject.

For Selah specifically, the consequence profile (Q9=High for doctrinal) means the framework's provenance hierarchy and HITL requirements are not optional enhancements -- they are architectural requirements that no off-the-shelf memory system provides. The custom extraction prompt that enforces pastoral provenance rules is the bridge between generic memory infrastructure and domain-specific safety.

This is the innovation opportunity: **a theologically-aware memory system that respects the authority structure of pastoral ministry.** The pastor's word is ground truth. Selah's inferences are provisional. The graph tracks relationships with the sensitivity that pastoral care demands. No existing product does this. The framework + Mem0/LightRAG + custom extraction is how you build it.

---

*Analysis by Atlas CTO | 2026-04-08 | Companion to knowledge-strategy-frameworkv3.md*
