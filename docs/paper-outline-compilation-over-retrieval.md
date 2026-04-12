# Paper Outline: Compilation Over Retrieval — A Prescriptive Knowledge Strategy Framework for Production Agent Systems

**Working Title Options:**
- "Compilation Over Retrieval: A Clinical Triage Model for Agent Knowledge Architecture"
- "The Three-Table Model: A Prescriptive Framework for Agent Knowledge Management in Production Systems"
- "When RAG Is Overkill: A Decision Framework for Agent Knowledge Strategy"

**Target Audience:** Practitioners building production agent systems — platform engineers, AI application developers, technical founders. Secondary audience: researchers studying agent memory architectures.

**Positioning:** The existing literature (particularly "Memory in the Age of AI Agents," Liu et al., 2025) provides comprehensive taxonomies of agent memory forms, functions, and dynamics. This paper complements that work by providing a prescriptive decision framework: given a specific deployment scenario, what knowledge architecture should you build? The contribution is not a new taxonomy but a diagnostic methodology — borrowed from clinical medicine — that maps deployment characteristics to engineering decisions.

---

## Abstract

Agent memory research has produced rich taxonomies but limited practical guidance for practitioners choosing among architectural approaches. Most production agent deployments operate in small-to-medium knowledge domains where the field's default assumptions — vector embeddings, retrieval-augmented generation, hybrid search — represent unnecessary complexity. We introduce a prescriptive decision framework organized as three interlocking diagnostic tables: knowledge kind (determining update semantics), a volume × dynamism matrix (determining engineering approach), and feature modifiers (determining operational constraints). The framework surfaces a principle we term *compilation over retrieval*: for bounded knowledge domains, investing in write-time knowledge compilation produces superior results to investing in read-time retrieval sophistication. We validate the framework against four production deployment profiles and demonstrate that the majority of real-world agent knowledge scenarios are better served by deterministic injection of compiled knowledge than by retrieval infrastructure.

---

## 1. Introduction

### 1.1 The Problem

The agent memory landscape is fragmented. Practitioners face a proliferation of frameworks, taxonomies, and implementation approaches with limited guidance on when to use which. The default industry posture — embed everything, vector-search everything, RAG everything — is driven by the assumption that retrieval is the hard problem. For many production deployments, this assumption is wrong. The hard problem is knowledge compilation: transforming raw information into curated, structured, injection-ready artifacts. Retrieval infrastructure solves a problem that most niche agent deployments don't have.

### 1.2 The Gap

Existing surveys (Liu et al., "Memory in the Age of AI Agents"; Zhang et al., multi-agent memory survey; the ICLR 2026 MemAgents workshop) provide descriptive taxonomies — what forms agent memory takes, what functions it serves, how it evolves. They catalog the landscape. What practitioners need is a map: given my specific deployment characteristics, what should I build? No existing work provides a prescriptive decision framework that maps deployment scenarios to architectural choices across the full lifecycle of ingestion, retrieval, and injection.

### 1.3 Contribution

We introduce the Three-Table Model, a diagnostic framework inspired by clinical triage methodology that separates three independent decision paths (ingestion, retrieval, injection) and provides prescriptive guidance through:

- **Table 1 (Knowledge Kind):** Classifying knowledge by its update semantics and natural query pattern — declarative, episodic, or procedural — independent of volume or implementation.
- **Table 2 (Volume × Dynamism Matrix):** A 3×4 grid that maps the two variables with the highest mechanical impact on implementation to named engineering patterns, each with specific prescriptions for ingestion, retrieval, and injection.
- **Table 3 (Feature Modifiers):** Operational concerns (provenance/trust, latency, consequence, consumer scope, growth rate) layered onto the base strategy as independent modifiers.

We articulate the *compilation over retrieval* principle: for knowledge domains below the wholesale injection threshold (~5,000 tokens), write-time compilation into curated artifacts eliminates the need for read-time retrieval infrastructure entirely. We argue this applies to the majority of production agent deployments.

### 1.4 Clinical Triage as Methodology

The framework borrows its structure from clinical diagnostic reasoning. A physician does not run every possible test on every patient. Instead, a triage process — a sequence of discriminating questions — narrows the diagnostic space and determines the treatment plan. The questions are ordered by discriminating power: primary triage (kind, volume, dynamism, provenance) determines the broad architectural category; secondary triage (temporal relevance, consumer scope, query pattern, latency, consequence, growth rate) refines the implementation. This methodology is standard in clinical practice and virtually absent in agent architecture.

---

## 2. Related Work

### 2.1 Agent Memory Taxonomies

- "Memory in the Age of AI Agents" (Liu et al., 2025) — Forms (token-level, parametric, latent), Functions (factual, experiential, working), Dynamics (formation, evolution, retrieval). Comprehensive descriptive taxonomy. Compare and contrast with our three-kind model (declarative, episodic, procedural): their "factual" maps to our "declarative," their "experiential" subsumes our "episodic" and "procedural" (we argue these should be separated because they have different update semantics), their "working" is our session-dynamic cell in the volume × dynamism matrix rather than a separate knowledge kind.

- Multi-agent memory surveys (TechRxiv 2025, ICLR MemAgents 2026 workshop) — Focus on shared vs. distributed memory paradigms, cache coherence, access control. Relevant to our consumer scope modifier but not to the core decision framework.

- MAGMA (Multi-Graph Agentic Memory Architecture, 2026) — Proposes multi-graph structures (semantic, temporal, causal, entity). Addresses the retrieval sophistication axis. Our framework would classify this as appropriate for the large-volume cells in Table 2 but unnecessary for small/medium deployments.

### 2.2 Production Agent Frameworks

- Hermes Agent (Nous Research) — Self-improving agent with skill extraction from experience, FTS5 cross-session recall, periodic memory nudges. Demonstrates procedural knowledge accumulation in practice. Relevant to our procedural knowledge kind and the system-observed provenance modifier.

- Letta/MemGPT — OS-inspired memory hierarchy (main context as RAM, external as disk). Tiered architecture analogous to our volume × dynamism approach but organized by access speed rather than knowledge characteristics.

- Mem0, Zep, Cognee — Production memory frameworks. Primarily focused on retrieval infrastructure (vector stores, knowledge graphs). Our framework argues these solve the right problem only for large-volume deployments.

### 2.3 What's Missing

No existing work:
1. Separates ingestion, retrieval, and injection as independent decision paths
2. Uses volume and dynamism as the primary engineering selectors
3. Provides named patterns (wiki pattern, growing journal, corpus pattern) with specific implementation prescriptions
4. Addresses multi-tenant deployment as a knowledge management problem
5. Articulates when retrieval infrastructure is unnecessary

---

## 3. The Three-Table Model

### 3.1 Foundational Concepts

#### 3.1.1 Three Decision Paths

Define ingestion, retrieval, and injection as independent decisions with different drivers. Demonstrate with examples where the same knowledge is ingested identically but retrieved and injected differently depending on context (e.g., a declarative fact stored in SQLite, retrieved by FTS5 in one scenario and injected wholesale in another).

#### 3.1.2 Knowledge as a Generic Term

Define scope: all information an agent system handles — external data, internal memory, session context, learned procedures, business documents, interaction history. The framework applies to all of these. The term "knowledge" is intentionally generic to avoid the fragmented terminology problem identified by Liu et al.

### 3.2 Table 1: Knowledge Kind

Three kinds defined by update semantics and natural query pattern:

- **Declarative** — "What is true?" Overwrite semantics. Categorical query pattern. Includes entity-linking facts as a subtype (affects storage/retrieval patterns but not epistemic category).
- **Episodic** — "What happened?" Accumulate semantics. Temporal query pattern (primarily), associative (secondarily).
- **Procedural** — "What works?" Refine semantics (or static if authored once). Pattern-match query pattern.

Discuss boundary cases: a compiled FAQ is declarative even though it was derived from episodic source material. The kind applies to knowledge *as stored and retrieved*, not to its origin.

### 3.3 Table 2: Volume × Dynamism Matrix

Define volume thresholds (small < ~5K tokens, medium ~5K–50K, large > ~50K). Define dynamism categories (static, interaction-dynamic, session-dynamic, event-driven).

Present the 3×4 matrix with named patterns:

| | Static | Interaction-dynamic | Session-dynamic | Event-driven |
|--|--------|---------------------|-----------------|--------------|
| Small | The Simplest Case | **The Wiki Pattern** | The Working Memory | The Notification Pattern |
| Medium | The Reference Library | The Growing Journal | The Pipeline Buffer | The Live Feed |
| Large | The Corpus | The Archive | (Warning sign) | The Firehose |

Each cell prescribes specific ingestion, retrieval, and injection approaches. Detailed description of each named pattern.

**Key insight:** The Wiki Pattern cell (small, interaction-dynamic) is where the *compilation over retrieval* principle is most clearly demonstrated. This cell prescribes: ingest via scheduled LLM compilation, store as structured files, retrieve by deterministic file-path lookup, inject wholesale. No vector search. No embedding pipeline. No retrieval infrastructure.

### 3.4 Table 3: Feature Modifiers

Five independent modifier categories, each layered onto the base strategy from Table 2:

1. **Provenance & Trust** — Human-authored, interaction-derived, agent-synthesized, system-observed. Determines ingestion gates, conflict handling, and audit requirements.
2. **Latency & Timing** — Real-time, interactive, deferred, batch. Constrains injection timing and retrieval mechanism.
3. **Consequence & Safety** — Low, medium, high. Determines review gates, attribution requirements, and fallback behavior.
4. **Consumer Scope & Visibility** — Single agent, multiple agents same tenant, single user multiple personas, cross-tenant. Determines access boundaries.
5. **Growth Rate & Lifecycle** — Bounded, linear, compounding. Determines compaction, pruning, and storage management.

### 3.5 How the Three Tables Work Together

Step-by-step methodology: classify by kind (Table 1), assess volume × dynamism (Table 2), layer on modifiers (Table 3). Worked examples demonstrating the complete diagnostic process.

---

## 4. The Compilation Over Retrieval Principle

This is the paper's central thesis and deserves its own section.

### 4.1 Statement of the Principle

For knowledge domains below the wholesale injection threshold (~5,000 tokens of relevant knowledge), investing in write-time compilation produces superior results to investing in read-time retrieval sophistication. A well-curated wiki with file-path lookup outperforms a poorly organized vector store with state-of-the-art retrieval.

### 4.2 Why the Field Defaults to Retrieval

RAG has become the default architecture for grounding agents in domain knowledge. This is appropriate for large-volume, heterogeneous corpora where the agent cannot know in advance which fragments will be relevant. But the RAG default has been applied uncritically to domains where it doesn't fit — small business knowledge bases, niche agent skill sets, personal preference stores. The field has over-indexed on retrieval sophistication and under-indexed on compilation quality.

### 4.3 The Compilation Alternative

Compilation inverts the effort profile: do the hard work at write time (LLM-driven extraction, deduplication, structuring, quality control) so that read time is trivial (deterministic file lookup, wholesale injection). The compilation pipeline is a batch process that runs when knowledge changes, not when the agent needs it. This means:

- Zero latency at query time (no LLM calls, no vector search, no network round-trips)
- Deterministic behavior (the same knowledge is injected every time, not a probabilistic retrieval result)
- Human-auditable artifacts (structured markdown pages, not opaque embedding vectors)
- Token cost amortized over compilation frequency, not per-session

### 4.4 When Compilation Works and When It Doesn't

Compilation works when: volume is small enough to inject wholesale after compilation, knowledge evolves slower than query frequency (you compile nightly but serve hundreds of sessions daily), the domain is structured enough for categorical organization (FAQ, policies, preferences), and the compilation output is auditable by a human operator.

Compilation breaks down when: the corpus is too large for wholesale injection, queries are genuinely semantically ambiguous (the user doesn't know what they're looking for), knowledge changes faster than compilation frequency (real-time data), or the domain is too heterogeneous for categorical organization.

### 4.5 The Volume Inflection Point

Where does compilation give way to retrieval? We argue the threshold is higher than most practitioners assume. A niche business agent's operational knowledge stabilizes at 5-15 pages after months of operation. A personal assistant's active declarative memory fits in ~1,000 tokens. Even medium-volume domains (a department's policy manual, a project's full documentation) can often be served by selective injection from compiled categories rather than retrieval search. The inflection point is not at hundreds of documents — it's at thousands. Below that, compilation plus deterministic selection outperforms RAG.

---

## 5. Validation: Four Production Deployment Profiles

Apply the complete three-table diagnostic to four real deployment scenarios, demonstrating that the framework produces specific, implementable prescriptions.

### 5.1 Profile A: Comprehensive Personal Assistant

Single-user, multi-persona agent (e.g., Brainiac/Atlas architecture). All three knowledge kinds present. Small volume per kind at any given time. Mixed dynamism. Framework prescribes: Tier 1 hot cache with FTS5 + recency (wiki pattern for declarative, working memory for session-dynamic), on-demand hybrid search for long-term episodic recall (growing journal pattern), static skill definitions (simplest case pattern). Demonstrates that even a sophisticated multi-tier architecture maps cleanly to the matrix.

### 5.2 Profile B: Small Business Voice Agent

Single-tenant, niche agent (e.g., plumbing company voice bot). Primarily declarative knowledge. Small volume. Real-time latency constraint. Framework prescribes: static bolus (simplest case), learned wiki (wiki pattern), pre-session wholesale injection. Zero retrieval infrastructure. Compilation over retrieval in its purest form.

### 5.3 Profile C: Multi-Tenant Agency Platform

Multi-tenant deployment with per-tenant knowledge isolation. Each tenant is Profile B with shared platform infrastructure. Framework prescribes: manifest-driven knowledge assembly, compilation subgraphs as opt-in platform services, deterministic pre-session injection per tenant. Demonstrates that the framework scales from single-tenant to multi-tenant by applying the same triage per tenant with shared engineering.

### 5.4 Profile D: Enterprise Deployment

Large-volume, high-consequence domain (hospital policy corpus, legal case database). Framework prescribes: full retrieval infrastructure (corpus pattern), layered search with fallback chain, RAG injection with source attribution. Demonstrates that the framework correctly identifies when retrieval investment is justified — the same framework that says "skip RAG for the plumber" says "build RAG for the hospital."

---

## 6. Anti-Patterns

Common architectural mistakes identified through the framework lens:

- **The Vector-Everything Fallacy** — Embedding all knowledge regardless of volume or query pattern
- **The Deep Hierarchy Fallacy** — Multi-agent delegation that burns tokens on context re-assembly at every hop
- **The Ephemeral Workflow Fallacy** — Discarding procedural knowledge from successful multi-agent workflows
- **The Retrieval-Over-Compilation Fallacy** — Investing in retrieval sophistication while under-investing in compilation quality
- **The Universal Architecture Fallacy** — Using the same memory architecture for all deployment profiles

---

## 7. Discussion

### 7.1 Relationship to Existing Taxonomies

Map the three-table model to the Forms-Functions-Dynamics framework of Liu et al. Show complementarity: their taxonomy describes what exists; ours prescribes what to build. Their "factual" and our "declarative" converge. Their "experiential" spans our "episodic" and "procedural" — we argue the split is necessary because overwrite vs. accumulate vs. refine are mechanically different operations. Their "working memory" is a dynamism category (session-dynamic) in our framework, not a knowledge kind.

### 7.2 Limitations

- Volume thresholds are approximate and context-dependent (model context window sizes are increasing, which shifts the "small" boundary upward)
- The framework addresses text knowledge only; multimodal knowledge adds dimensions not covered
- Compilation quality is asserted as the bottleneck but not empirically measured in this paper
- The clinical triage metaphor is structural, not a claim of equivalent rigor

### 7.3 Future Work

- Empirical measurement of compilation quality vs. retrieval sophistication in controlled deployments
- Extension to multimodal knowledge (images, audio, structured data)
- Automated triage: can an agent system self-diagnose its knowledge profile and select its own architecture?
- Benchmarking the volume inflection point: at what corpus size does retrieval outperform compilation + selective injection?

---

## 8. Conclusion

The agent memory field has rich taxonomies but limited prescriptive guidance. The Three-Table Model provides a diagnostic framework that practitioners can apply to any deployment scenario to determine the appropriate knowledge architecture. The central finding is that most production agent deployments operate in knowledge domains where the field's default retrieval-centric approach is unnecessary. For these domains, compilation over retrieval — investing in write-time knowledge curation rather than read-time search sophistication — produces simpler architectures, lower latency, deterministic behavior, and human-auditable knowledge artifacts. The framework doesn't argue against retrieval infrastructure; it argues for knowing when you need it and when you don't.

---

## Appendix A: The Ten Triage Questions (Quick Reference)

Numbered list with brief description of each question and what decision path it primarily drives.

## Appendix B: Volume × Dynamism Matrix (Full Cell Descriptions)

Complete prescriptions for all 12 cells with ingestion, retrieval, and injection guidance.

## Appendix C: Worked Examples

3-4 complete walk-throughs of the diagnostic process applied to specific knowledge artifacts, showing all three tables in sequence.
