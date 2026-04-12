This is a great framing — clinical triage as the metaphor for memory architecture decisions. Let me work through what I think the discriminating questions are, and then you can push back on whether I'm missing any or weighting them wrong.

**The Triage Questions**

**1. What is the knowledge volume?**

This is your first branch point, analogous to "is the patient stable or unstable?" It determines whether you can inject knowledge wholesale or need selective retrieval. The thresholds I'd propose: small is under ~5,000 tokens (fits in a system prompt injection), medium is 5K–50K tokens (exceeds a single injection but fits in a context window with selection), and large is 50K+ (requires retrieval infrastructure). Most niche business agents live in "small" and never leave it. That's the insight your PRD reflects.

**2. How static or dynamic is the knowledge?**

This is the acuity question — is this a chronic stable condition or an acute evolving one? Static knowledge changes on human timescales (quarterly, annually — company policies, product catalogs, onboarding docs). Dynamic knowledge changes on interaction timescales (every call, every session — learned facts, customer preferences, corrections from the business owner). This drives whether you invest in ingestion infrastructure or just re-ingest manually when things change.

**3. What is the provenance of the knowledge?**

Who is the authority? This maps to your bolus-vs-wiki distinction. Owner-provided knowledge (the business told you this) has different trust levels, correction pathways, and update mechanisms than interaction-derived knowledge (you learned this from calls). A third category is agent-synthesized knowledge (the agent inferred or compiled this from raw data). Provenance determines who can correct it, how conflicts are resolved, and whether human review is needed before the knowledge is trusted.

**4. What is the temporal relevance pattern?**

Does the consumer of this knowledge need "what is true right now" or "what was true at a point in time"? Current-state queries ("do we service Kingsport?") need the latest version of a fact, and old versions are noise. Temporal queries ("what was I working on last month?") need time-indexed recall where older entries are the point. This is the clearest separator between your wiki pattern (current-state) and your Tier 3 pattern (temporal).

**5. Who is the consumer of the knowledge?**

Is this knowledge consumed by a single persona/agent, by multiple agents serving the same tenant, or across tenants? Single-consumer knowledge can be injected directly. Multi-agent knowledge needs a shared access layer. Cross-tenant knowledge is analytics, not memory. This maps to your visibility rules — the sector-based read permissions in Brainiac (episodic is persona-scoped, semantic is shared).

**6. What is the query pattern?**

How does the knowledge get asked for? Categorical queries ("what's our rebate policy?") are exact-match or keyword problems — FTS5 or even a file path lookup. Associative queries ("that thing we discussed about the deployment strategy") are semantically fuzzy — this is where vector similarity earns its keep. Temporal queries ("last month," "last week") are time-range filters. Exhaustive queries ("give me everything about this customer") are full scans within a scope. The query pattern determines the retrieval mechanism, not the other way around.

**7. What is the acceptable latency?**

Is this a voice agent where 200ms matters, a chat agent where 2 seconds is fine, or a batch process where minutes are acceptable? Voice pushes you hard toward pre-computed injection (your wiki pattern). Chat can tolerate a tool-call retrieval step. Batch (nightly compilation, lint operations) can afford full-corpus scans and LLM-driven extraction.

**8. What is the consequence of stale or wrong knowledge?**

This is severity of illness. If the agent gives a wrong answer about a service area, a customer gets a bad experience but it's recoverable. If the agent gives wrong medical information or wrong pricing that results in a contractual commitment, the consequences are different. High-consequence knowledge demands human-in-the-loop verification, audit trails, and source attribution. Low-consequence knowledge can be auto-compiled and auto-injected without review.

**9. What is the expected growth rate?**

A plumber with 5 calls/day accumulates knowledge slowly. A customer support center with 500 calls/day accumulates fast. Growth rate determines whether your storage and retrieval architecture needs to be designed for scale or whether "it fits in a file" is a permanent answer. This also affects your compaction and summarization strategy — high-growth domains need aggressive summarization to keep the knowledge bolus from bloating past your injection budget.

**10. Is the knowledge structured or unstructured?**

Structured knowledge has clear categories, taxonomies, and fields (service areas, hours, pricing tiers). Unstructured knowledge is narrative (conversation transcripts, meeting notes, journal entries). Structured knowledge is better served by deterministic lookup (YAML, markdown with frontmatter, indexed tables). Unstructured knowledge is where search — whether FTS5 or vector — becomes necessary because you can't pre-categorize it cleanly.

---

Those are my ten. I'd rank the first four (volume, dynamism, provenance, temporal pattern) as the primary triage — they determine the broad architectural category. The remaining six are secondary — they refine the implementation within that category.

Before we start mapping these to tier assignments and ingestion/query strategies, what's your read? Am I missing a discriminating question, or is one of these not actually doing work in the decision tree?



You're right to separate ingestion and retrieval as distinct decision paths. They correlate, but they aren't the same decision. The choice to vector-embed at ingestion time is a commitment — it's saying "I anticipate needing semantic retrieval later." But you might ingest something as structured markdown and later realize you need fuzzy retrieval over it, or you might embed something and never query it semantically because FTS5 always gets there first. The triage questions should independently inform both paths.

Let me also pick up on something important you just said: maybe it isn't tiered. That's worth sitting with. Your Brainiac architecture uses tiers, but the tiers are really an implementation decision driven by the answers to the triage questions, not a universal taxonomy. A tier implies hierarchy — Tier 1 is "closer" or "hotter" than Tier 3. But knowledge doesn't always organize hierarchically. Some knowledge is hot and small (session context). Some knowledge is cold and small (a policy that rarely changes but must be exact when needed). Some knowledge is hot and large (a high-volume call center's daily learnings). The tier model works for Brainiac because your personal agent has a specific profile across the triage questions — but a different profile would produce a different topology.

So let me reframe. Instead of starting with tiers and mapping knowledge into them, let's start with the triage questions and see what natural groupings emerge from the answers. Here's how I'd structure this:

**The Two Decision Paths**

**Path A: Ingestion — "How should this knowledge enter the system?"**

The ingestion decision is about transformation and storage format. When knowledge arrives (from a document, a transcript, a user statement, an API response), the system has to decide how to process it and where to put it. The triage questions that most directly drive ingestion are:

Volume determines whether you can store the knowledge verbatim or need to summarize/compile it. A 2-page FAQ can be stored as-is. Three months of call transcripts need compilation into distilled pages. This is the difference between your static bolus (store the document) and your wiki compiler (LLM-distill the transcripts).

Dynamism determines the ingestion trigger. Static knowledge is ingested once (onboarding) or on human-initiated re-ingestion. Dynamic knowledge needs an automated pipeline — your nightly compiler, your after-every-interaction fact extractor, your compaction-at-30-messages trigger.

Provenance determines the trust level at ingestion. Owner-provided knowledge is ingested as ground truth. Interaction-derived knowledge is ingested as provisional (needs confirmation patterns, your lint operation). Agent-synthesized knowledge is ingested with the lowest confidence and the highest need for human review.

Structure determines the storage format. Structured knowledge (service areas, hours, pricing) should be ingested into structured formats — markdown with frontmatter, YAML, indexed SQLite columns. Unstructured knowledge (conversation summaries, journal entries) may warrant embedding at ingestion time because you're anticipating fuzzy retrieval.

Growth rate determines whether you need compaction/summarization as part of the ingestion pipeline. Low-growth domains can accumulate indefinitely. High-growth domains need your compaction pattern: summarize, promote, prune.

**Path B: Retrieval — "How should this knowledge reach the consumer?"**

The retrieval decision is about selection and delivery. When an agent needs knowledge (at session start, mid-conversation, or in a batch process), the system has to decide what to fetch and how. The triage questions that most directly drive retrieval are:

Volume determines whether you retrieve everything (wholesale injection) or select a subset. Under ~5K tokens, inject it all — your `assemble_wiki_context()` pattern. Above that, you need a selection mechanism, and the next questions determine which one.

Query pattern determines the retrieval mechanism. Categorical queries use deterministic lookup (file path, index key, exact SQL match). Associative queries use search (FTS5 for keyword, vector for semantic). Temporal queries use time-range filters. The mechanism should match the pattern, not the other way around.

Temporal relevance determines whether you retrieve the latest version or a historical range. Current-state retrieval wants the most recent authoritative answer. Temporal retrieval wants a time-windowed scan. This is the difference between "read the current service-area.md" and "query Tier 3 for episodic entries from last month."

Latency determines the retrieval timing. Voice agents need pre-computed injection (assemble before the session starts). Chat agents can tolerate mid-conversation tool calls. Batch processes can run full hybrid searches. This is your `injection_strategy` field in the manifest: `pre-session`, `tool-query`, or `both`.

Consumer scope determines the retrieval boundary. Single-persona retrieval can include everything in scope. Multi-persona retrieval needs visibility rules (your sector-based read permissions). Cross-tenant retrieval is a different system entirely.

Consequence of error determines the retrieval confidence threshold. High-consequence domains need source attribution, provenance tracking, and possibly human confirmation before the agent acts on retrieved knowledge. Low-consequence domains can inject and trust.

**What I think the next step is:**

Before we jump to a table or a tier model, I think we need to define the knowledge profiles that emerge from these triage answers. A profile is a specific combination of answers — like a clinical presentation. "Small volume, static, owner-provided, current-state, categorical queries, low latency, low consequence" is one profile. "Growing volume, dynamic, interaction-derived, temporal, associative queries, latency-tolerant, low consequence" is another. Each profile maps to a specific ingestion strategy and a specific retrieval strategy.

Your Brainiac Tier 1 is one profile. Your Tier 3 is another. Your wiki PRD is a third. But they aren't hierarchical — they're different presentations that call for different treatment plans.

Want to enumerate the profiles you think are real-world relevant? I'd rather build the taxonomy from actual use cases you're deploying than from abstract combinations. The plumbing company voice agent, Brainiac, and the eventual enterprise deployment each have distinct profiles, and mapping them explicitly would ground this before we formalize it.



You're right — injection is a third distinct decision path. I conflated it with retrieval, but they're not the same thing.

Let me sharpen the distinction:

**Retrieval** is the act of finding and selecting knowledge from storage. It answers "what knowledge is relevant right now?" The output of retrieval is a set of candidate knowledge fragments.

**Injection** is the act of delivering that knowledge into the LLM's context window. It answers "how and when does this knowledge reach the model?" The output of injection is a shaped context payload.

The reason they're separate decisions is that you can retrieve the same knowledge but inject it differently depending on the situation. You might retrieve a customer's preference page via file lookup, but inject it as part of the system prompt (pre-session), or as a tool response mid-conversation, or as a structured prefix before the user's message. The retrieval mechanism was identical — the injection strategy differed.

Injection also has its own constraints that retrieval doesn't: token budget (how much can you inject before you crowd out reasoning space), placement (system prompt vs. conversation history vs. tool result — each has different attention weight for the model), timing (before the session, on-demand during the session, or continuously refreshed), and shaping (do you inject the raw knowledge or a compiled summary of it).

So the three decision paths are:

 **Ingestion** : How knowledge enters and is stored. Driven by volume, dynamism, provenance, structure, growth rate.

 **Retrieval** : How knowledge is found and selected. Driven by volume, query pattern, temporal relevance, consumer scope.

 **Injection** : How knowledge is delivered to the model. Driven by latency, token budget, session lifecycle, consequence of error.

Now let me map the four use cases across all three paths. I want to do this as profiles first — the clinical presentation for each — and then we can see what patterns emerge.

---

**Use Case 1: Brainiac — Comprehensive Personal Assistant**

*Ingestion profile:* The knowledge is multi-source. Static identity and preferences are authored by hand (ATLAS_CLAW.md files, knowledge base markdown). Dynamic facts are extracted after every interaction by a background LLM pass — fire-and-forget, subject-predicate-object triples. Episodic summaries are generated by compaction when conversation history hits 30 messages. Growth rate is moderate — a power user generates maybe 5-15 facts per day, one journal entry per extended session. Provenance is single-authority (you). Structure is mixed: the reference docs are structured markdown, the extracted facts and journal entries are unstructured text. Ingestion uses both direct storage (Tier 1 verbatim write) and transformation (LLM summarization for compaction, LLM extraction for facts). Embeddings are generated at ingestion time for Tier 3 because associative retrieval is anticipated.

*Retrieval profile:* Queries are mixed. Most daily retrieval is deterministic — load the persona's CLAUDE.md, load recent memories by recency, FTS5 match against the current message. Tier 3 hybrid search (FTS5 + vector with RRF fusion) activates only on temporal or associative queries. The volume at Tier 1 is deliberately kept small (your retrieval budget is ~1,000 tokens, 8 items max). Tier 3 volume grows unbounded but is queried infrequently and on-demand. Consumer is a single user with multiple personas, so visibility rules apply (semantic shared, episodic persona-scoped).

*Injection profile:* Automatic injection at every conversation turn for Tier 1 — recent memories and FTS5 matches are prepended to the context. Tier 1.5 reference docs are available but loaded on-demand by the agent reading files. Tier 2 project satellites inject automatically based on working directory detection. Tier 3 is on-demand only via `/recall` command — never auto-injected. Placement is system prompt for identity (ATLAS_CLAW.md) and conversation-adjacent for retrieved memories. Token budget is tightly controlled: ~1,000 tokens for memory injection, well under 1% of the context window. Latency is tolerant (Telegram, not voice).

---

**Use Case 2: Plumbing Company Voice Agent**

*Ingestion profile:* Two distinct knowledge sources with different ingestion paths. The static bolus is owner-provided documents ingested once at onboarding — currently uses a RAG pipeline with cosine similarity, but as your PRD argues, the volume probably doesn't justify it. The learned wiki is interaction-derived, compiled nightly by an LLM batch job from call transcripts. Growth rate is low (a plumber gets 5-10 calls/day, the wiki stabilizes at 5-15 pages within months). Provenance is bifurcated: the bolus is owner-authority, the wiki is interaction-derived with owner-confirmation as the trust escalation. Structure is high for the wiki (markdown with frontmatter, categorized into concepts and FAQ) and variable for the bolus (depends on what the owner provides). No embeddings at ingestion — the volume doesn't warrant it.

*Retrieval profile:* Almost entirely deterministic. The FAQ file, the service area page, the scheduling policies page — these are known paths loaded by file existence check. Caller-specific retrieval is keyed by caller ID. No search engine needed for the common path. A `tool-query` fallback exists in the architecture for edge cases (questions outside the injected pages), but it's a Phase 3 feature, not core. The volume is small enough that "retrieve everything relevant" is cheaper than "search for the right fragment."

*Injection profile:* Pre-session wholesale injection. Before the caller connects, `assemble_wiki_context()` reads the relevant files and prepends them to the system instruction at WebSocket connection time. No mid-call retrieval in the MVP. Hard cap at 3,000 tokens (~12K characters). Latency is critical — voice agents can't tolerate a retrieval round-trip after the caller is connected. Placement is system instruction (Gemini Live's equivalent of system prompt). The injection is deterministic and pre-computed — zero LLM calls at retrieval or injection time.

---

**Use Case 3: Multi-Agent Framework**

*Ingestion profile:* This is where it gets interesting because you have knowledge flowing between agents, not just between a user and an agent. Each agent in the framework produces outputs that become inputs to other agents. A research agent's findings become a planning agent's context. A planning agent's decisions become an execution agent's instructions. Ingestion is continuous and inter-agent — not batch, not human-initiated. Provenance is multi-source: some knowledge originates from external APIs (research), some from other agents (inter-agent communication), some from the user (directives). The trust hierarchy matters: user directives override agent-synthesized knowledge, which overrides external data. Structure varies by agent output — some produce structured JSON, some produce narrative summaries. Volume per agent is small, but the aggregate across the pipeline can be significant. Growth rate is session-bounded: multi-agent workflows typically run to completion and then the intermediate knowledge is disposable. The durable output is the final deliverable, not the inter-agent chatter.

*Retrieval profile:* Mostly pass-through — the output of one agent is directly injected into the next agent's context. There's no "search" step in a well-designed pipeline because the orchestrator knows which outputs flow to which inputs. Retrieval becomes relevant only when an agent needs to reference something outside the current pipeline — historical project context, user preferences, domain knowledge. That's where a shared memory layer (your Tier 1 semantic facts, visible across personas) comes in. Query pattern is predominantly categorical: "what did the research agent find about X" is a direct lookup, not a fuzzy search.

*Injection profile:* This is the token cost problem you identified with Paperclip. Every agent handoff is a full context assembly: system prompt + agent instructions + relevant prior outputs + the current task. If you're injecting everything from every upstream agent, you pay the context-window tax at every hop. The efficient injection strategy is selective — only inject the outputs from upstream agents that are directly relevant to the current agent's task, not the entire conversation history. Shaping matters enormously: injecting a raw 5,000-token research report into a planning agent is wasteful if a 500-token summary would suffice. The injection decision here is really a compilation decision — how aggressively do you summarize inter-agent outputs before passing them downstream. Latency is moderate (not voice, but the user is waiting for the pipeline to complete).

---

**Use Case 4: Enterprise Deployment**

*Ingestion profile:* Volume is the defining characteristic. A hospital system's policy corpus, a law firm's case database, a manufacturer's product catalog — we're talking tens of thousands of documents, potentially millions of knowledge fragments. Ingestion can't be manual; it requires automated pipelines with chunking, indexing, and likely embedding. Dynamism is mixed: some knowledge is stable (HR policies, regulatory requirements), some changes frequently (pricing, inventory, active cases). Provenance is institutional — multiple authors, multiple departments, version-controlled documents with formal approval chains. Structure is highly variable across the corpus: some documents are structured (forms, databases), some are narrative (legal briefs, clinical notes). Growth rate is high and sustained. This is the one use case where vector embeddings at ingestion are genuinely justified — the volume makes wholesale injection impossible and deterministic path-based retrieval insufficient because you can't pre-enumerate all the paths a query might need.

*Retrieval profile:* This is where retrieval infrastructure actually earns its keep. Queries span a large heterogeneous corpus where the user may not know exactly what they're looking for or where it lives. Hybrid search (FTS5 + vector) is justified. But even here, I'd argue the retrieval should be layered: try categorical/deterministic first (if the query maps to a known document category), fall back to FTS5 keyword search, and use vector similarity only when the first two fail or when the query is genuinely semantically ambiguous. The retrieval result set needs ranking, deduplication, and possibly re-ranking by an LLM before injection.

*Injection profile:* Selective and shaped. You can't inject a 50-page policy document wholesale; you inject the relevant sections. Retrieval-augmented generation (RAG) in its traditional sense applies here: retrieve chunks, inject as context, generate a response grounded in the chunks. Token budget management is critical because the corpus is large enough that naive retrieval returns too much. Placement is typically as retrieved context blocks with source attribution. Latency depends on the interface (chat vs. internal tool vs. batch report). Consequence of error is often high (legal, medical, financial), so source attribution and confidence scoring become mandatory, not optional.

---

**Patterns I see emerging across the four profiles:**

The volume question really is the primary branch point, and it creates two fundamentally different worlds. Below the injection threshold (roughly 5K tokens of total relevant knowledge), you can skip retrieval entirely and just inject everything — your wiki pattern. Above it, you need selection, and the selection mechanism depends on the query pattern and the knowledge structure.

Dynamism determines whether ingestion is a one-time event or an ongoing pipeline. But it also interacts with injection: dynamic knowledge needs freshness guarantees at injection time (are you injecting the latest version?), while static knowledge can be cached.

The inter-agent case (Use Case 3) is genuinely different from the others because the "knowledge" is ephemeral pipeline state, not durable memory. It probably shouldn't be modeled in the same memory system at all — it's more like function arguments than like institutional knowledge.

Do you want to take these four profiles and start extracting the decision table? I'm thinking a matrix where the rows are the triage questions and the columns show how each question maps to a specific ingestion strategy, retrieval strategy, and injection strategy — essentially your recipe for "given these triage answers, here's the treatment plan."



That's a strong pushback and I think you're right. Let me reconsider.Okay, Hermes is very relevant here. Your pushback is correct and it exposes a gap in my thinking. Let me revise.

I was treating inter-agent knowledge as ephemeral pipeline state — like function arguments that get garbage collected after the workflow completes. But that's only true for the *data* flowing through the pipeline. The *patterns* — the workflow itself, the approach that worked, the sequence of steps that solved a class of problem — that's durable knowledge. And Hermes makes this explicit by promoting successful workflows into skill files that persist and improve over time.

Your surgery analogy is exactly right. A surgeon doesn't just remember the outcome of each operation (episodic memory). They internalize the technique — the procedural knowledge of "when the anatomy presents like this, this approach works." That's a different kind of knowledge than facts or episodes. It's a third category:  **procedural knowledge** , or what Hermes calls skills.

So let me revise the knowledge taxonomy. We're not just dealing with facts and episodes. We have at least four kinds of knowledge, and they each have different ingestion, retrieval, and injection profiles:

**Declarative knowledge** — facts, policies, preferences. "We don't service north of Highway 36." "The user prefers PostgreSQL." This is your semantic sector in Brainiac and your static bolus + wiki concepts in the PRD.

**Episodic knowledge** — time-indexed records of what happened. "Last Tuesday we debugged the Nginx config for two hours." "Mrs. Johnson called and asked for Dave." This is your episodic sector in Brainiac and the raw transcripts that feed the wiki compiler.

**Procedural knowledge** — reusable approaches for recurring situations. "When deploying to production, run tests first, then build the Docker image, then push." "When a caller asks about the rebate, confirm it's still active, then explain the paperwork process." This is what Hermes extracts as skills. Your Brainiac skill system (YAML skill files with a skill-creator) is the same concept — but you author them manually rather than having the system extract them from experience.

**Relational knowledge** — who knows what, who prefers what, how entities connect. "Mrs. Johnson prefers Dave." "The CTO persona handles infrastructure questions." "Agent A's research output feeds Agent B's planning input." This is implicit in your current systems but not explicitly modeled as its own category.

This changes the triage questions. Question 10 (structured vs. unstructured) might actually be better framed as **"What kind of knowledge is this?"** — declarative, episodic, procedural, or relational — because the kind determines the natural storage format, the ingestion transformation, and the retrieval pattern more precisely than the structured/unstructured binary does.

And it directly addresses your pushback about inter-agent memory. In a multi-agent framework, the procedural knowledge ("this workflow pattern worked for this class of problem") is the most valuable durable output, not the intermediate data. Discarding it is like a surgical residency program that never lets residents observe or learn technique — every operation starts from first principles.

So here's my revised triage list with the separation of ingestion, retrieval, and injection as distinct paths, and with knowledge kind added:

**Primary Triage (determines the broad strategy):**

1. **What kind of knowledge is it?** Declarative, episodic, procedural, or relational. This is the new first question because it determines the natural shape of everything downstream.
2. **What is the volume?** Small (fits in a prompt injection), medium (fits in a context window with selection), large (requires retrieval infrastructure). But volume should be assessed *per kind* — you might have small declarative knowledge but large episodic knowledge for the same tenant.
3. **How dynamic is the knowledge?** Static (changes on human timescales), session-dynamic (changes during a conversation), interaction-dynamic (evolves across conversations over time), or event-driven (changes in response to external triggers).
4. **What is the provenance?** Human-authored (highest trust), interaction-derived (needs confirmation), agent-synthesized (lowest trust, needs review), or system-observed (patterns extracted from behavior, like Hermes's skill creation trigger of "five or more tool calls + success").

**Secondary Triage (refines implementation):**

5. **What is the temporal relevance pattern?** Current-state (only the latest version matters), historical (time-indexed recall), or cumulative (knowledge improves/refines over time, like a skill that gets better with each execution).
6. **Who is the consumer?** Single agent, multiple agents (same tenant), cross-tenant, or the human operator (dashboard, audit).
7. **What is the query pattern?** Categorical (exact lookup), associative (fuzzy/semantic), temporal (time-range), exhaustive (full scan within scope), or pattern-matching (does the current situation match a known skill/procedure).
8. **What is the acceptable latency?** Real-time (voice), interactive (chat), deferred (tool call), or batch (nightly compilation).
9. **What is the consequence of stale or wrong knowledge?** Low (bad customer experience, recoverable), medium (inefficiency, wasted work), high (financial/legal/medical impact).
10. **What is the expected growth rate?** Bounded (stabilizes, like a plumber's wiki), linear (grows proportionally to usage), or compounding (grows faster than usage, like a skill library that generates derivative skills).

Now, the key revision based on your pushback: procedural knowledge — skills — is the bridge between what I was dismissing as ephemeral inter-agent state and what's actually durable institutional capability. A multi-agent workflow that succeeds should deposit its pattern into the procedural knowledge store so that next time, the system doesn't re-derive the approach from scratch. That's not the same memory system as "what did Mrs. Johnson ask for" (declarative) or "what happened last Tuesday" (episodic), but it absolutely belongs in the same unified knowledge framework. It's just a different kind, with its own ingestion trigger (successful completion of a non-trivial workflow), its own retrieval pattern (pattern-match the current situation against known skills), and its own injection strategy (load the skill definition into the system prompt when a matching situation is detected).

Does this revised taxonomy feel right, or is the four-kind model still missing something? I want to make sure the foundation is solid before we start building the decision table that maps triage answers to specific ingestion/retrieval/injection strategies.
