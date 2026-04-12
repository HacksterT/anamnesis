---
title: "Anamnesis -- Monetization and Go-to-Market Strategy"
created: 2026-04-09
related: "anamnesis-framework.md, anamnesis-construction.md, anamnesis-behavioral-mining.md"
---

# Anamnesis -- Monetization and Go-to-Market Strategy

## The Thesis

Open source the framework. Monetize the application. The framework builds credibility and adoption. The application builds revenue. They reinforce each other.

The AI industry is moving toward proprietary memory lock-in. Anthropic's Conway project, OpenAI's persistent memory, Google's session state -- all bet that behavioral context becomes a switching cost the user can never escape. Anamnesis is the counter-position: your memory should be portable, self-hosted, inspectable, and yours. Publishing that position as open source gives it credibility that a proprietary product never could. You cannot credibly argue against lock-in while locking people in.

---

## Two Layers, Two Models

### Layer 1: Anamnesis Framework (Open Source)

The framework is the three core documents and the Python library. The five-circle model, the triage questions, the compilation pipeline, the reconciliation model, the bolus architecture, the transport layer inversion. This is the engine.

**License:** MIT or Apache 2.0. Permissive. No copyleft. Businesses can use it without legal friction. The goal is adoption, not control.

**What's included:**
- The framework documents (strategy, construction, behavioral mining)
- The Python library (`knowledge-framework` package)
- Default extraction prompt templates
- Example configurations for common use cases
- Built-in micro-pipeline templates for behavioral mining

**What's not included:**
- Production deployment tooling (that's the platform)
- Tenant management and isolation (that's the platform)
- Dashboard UI for reconciliation (that's the platform)
- Managed compilation pipeline (that's the platform)

**Value to the community:**
- Developers building agent memory systems get a principled framework instead of reinventing the wheel
- The five-circle model becomes a shared vocabulary for discussing memory architecture
- The triage questions give developers a decision process they can apply to their own use cases
- The transport layer inversion and intent resolution layer give developers a better pattern for skill/tool architecture

**Value to you:**
- Authority and credibility in the agent memory space
- Community contributions (new storage backends, compilation modes, micro-pipelines)
- Hiring signal (contributors become potential collaborators)
- Content pipeline (the framework generates blog posts, conference talks, and technical writing naturally)
- The-agency's technical claims become verifiable ("built on Anamnesis" means something when the framework is public and inspectable)

### Layer 2: The-Agency Platform (Paid SaaS)

The-agency is Anamnesis applied to a specific, paying vertical: small business voice agents that learn from customer interactions. The business owner doesn't know or care about five circles. They care that their agent gets smarter and they don't have to do anything.

**What the platform provides on top of the framework:**
- Multi-tenant isolation (per-tenant circles, per-tenant compilation, per-tenant behavioral profiles)
- Managed compilation pipeline (nightly runs, cost optimization, model selection per tenant)
- Business owner dashboard (reconciliation UI, behavioral profile viewer, FAQ review, "your agent learned 3 things this week")
- Onboarding flow (business information intake that populates Circle 1 and Circle 2 automatically)
- Voice agent runtime (Gemini Live integration, Twilio bridge, real-time injection assembly)
- Billing and metering (per-tenant usage tracking, compilation cost allocation)
- Support and SLA

**Pricing model:** Per-tenant monthly subscription. The compilation pipeline has real LLM costs (~$0.30-0.60 per tenant per night for active tenants). The platform absorbs these and builds them into the subscription price with margin. Tiers based on call volume, number of boluses, and compilation frequency.

| Tier | Monthly | Includes | Target |
|------|---------|----------|--------|
| Starter | $99 | 1 voice agent, 500 calls/month, nightly compilation, 5 boluses, basic dashboard | Solo trades (plumber, electrician, HVAC) |
| Professional | $249 | 2 agents, 2,000 calls/month, nightly compilation, 15 boluses, full dashboard, behavioral mining | Small businesses with front desk needs |
| Business | $499 | 5 agents, 10,000 calls/month, custom compilation prompts, unlimited boluses, API access | Multi-location businesses, franchises |
| Enterprise | Custom | Custom agent count, custom integrations, dedicated support, SLA | Regional chains, chambers of commerce |

These are starting points. Adjust based on actual cost data once compilation and call volume are measurable.

---

## The Open Source Flywheel

The framework and the platform create a reinforcing cycle:

```
Anamnesis published open source
    │
    ├─→ Developers adopt the framework
    │     ├─→ Community contributions improve the library
    │     ├─→ Bug reports and edge cases harden the code
    │     └─→ Adoption creates awareness
    │
    ├─→ Content and credibility
    │     ├─→ Blog posts, talks, technical writing
    │     ├─→ "Built on Anamnesis" becomes a trust signal
    │     └─→ HacksterT becomes the authority on agent memory
    │
    ├─→ The-agency benefits
    │     ├─→ Technical claims are verifiable (open source framework)
    │     ├─→ Platform improvements flow back to the framework
    │     ├─→ Enterprise customers see the framework, buy the platform
    │     └─→ Competitive moat: the learning agent, not the static agent
    │
    └─→ Counter-narrative to proprietary lock-in
          ├─→ Positions HacksterT as the alternative voice
          ├─→ Attracts developers and businesses who value data ownership
          └─→ Press and community goodwill
```

---

## Revenue Streams

### Primary: Platform Subscriptions (the-agency)

Recurring monthly revenue from small businesses using voice agents. The learning capability (Anamnesis-powered) is the retention mechanism. The longer a business uses the platform, the smarter the agent gets, the harder it is to switch. But unlike Conway, the lock-in is in the accumulated knowledge (which the business owns and can export), not in the platform's proprietary infrastructure.

**Revenue targets (conservative):**

| Timeline | Tenants | Avg Revenue/Tenant | MRR | ARR |
|----------|---------|-------------------|-----|-----|
| Month 6 | 5 | $150 | $750 | $9,000 |
| Month 12 | 20 | $175 | $3,500 | $42,000 |
| Month 18 | 50 | $200 | $10,000 | $120,000 |
| Month 24 | 100 | $200 | $20,000 | $240,000 |

These assume a solo operator (you) with no sales team. Growth comes from the Kingsport/Johnson City market first, then regional expansion via chamber of commerce partnerships and word of mouth.

### Secondary: Consulting and Implementation

Enterprise customers who want Anamnesis applied to their specific domain. A hospital system that wants the five-circle model for clinical decision support. A law firm that wants curated case knowledge with the reconciliation model. A mid-size company that wants behavioral mining for employee productivity tools.

This is where your clinical informatics background is the differentiator. You're not a developer selling a memory library. You're a physician-informaticist who built a knowledge architecture from clinical principles and can apply it to complex domains. That's a different conversation at a different price point.

**Rate:** $200-300/hour or project-based. Not the primary revenue stream, but high-margin when it happens.

### Tertiary: Vertical Bolus Marketplace (Future)

Once Anamnesis has adoption and the-agency has multiple tenants in the same vertical, a marketplace for pre-built knowledge boluses becomes viable. A "plumbing best practices" bolus. A "dental front desk FAQ" bolus. A "HVAC seasonal maintenance" bolus. These are vertical knowledge sets that new tenants can plug in on day one instead of building from scratch.

**Model:** Revenue share or flat fee per bolus. The platform provides the marketplace; domain experts (or the compilation pipeline aggregating anonymized cross-tenant patterns) provide the boluses.

This is speculative and depends on having enough tenants to generate cross-tenant insight. Don't build it until the primary revenue stream is established.

---

## Content Strategy

The framework generates content naturally. Each concept is a standalone piece:

**Blog posts / articles:**
- "The Medication Reconciliation Model for AI Memory" -- clinical analogy applied to agent knowledge curation. Targets the AI/ML audience that reads practical architecture pieces.
- "Why Your Agent Doesn't Need to Know Everything About You" -- the 80/20 behavioral mining argument. Counter-narrative to the "always-on AI" trend. General audience appeal.
- "The Transport Layer Inversion" -- technical piece on moving MCP from tool boundary to skill boundary. Developer audience. Likely to generate discussion.
- "Five Circles: A Trust Gradient for Agent Memory" -- the conceptual model overview. Framework-level piece.
- "Knowledge Boluses: Plug-and-Play Memory for AI Agents" -- the bolus concept explained. Practical, developer-oriented.

**Where to publish:**
- Personal blog or Substack (own the platform)
- Cross-post to dev.to, Hacker News, LinkedIn
- The Anamnesis GitHub repo README links to the articles
- Voice of Repentance connection for the faith/values intersection pieces (the liturgical meaning of anamnesis)

**Conference talks (when ready):**
- Local tech meetups first (Johnson City, Knoxville, Asheville)
- AI/ML conferences (submissions after the framework is published and has some adoption)
- Clinical informatics conferences (AMIA, HIMSS) -- the clinical-to-AI crossover is unique and memorable

---

## Competitive Positioning

| Competitor | Their Bet | Anamnesis Counter |
|-----------|-----------|-------------------|
| Anthropic (Conway) | Always-on observation, proprietary behavioral model, platform lock-in | Open, portable, user-owned memory. You export your knowledge when you leave. |
| Mem0 | Universal memory layer, vector-everything, one architecture for all use cases | Triage-driven architecture. Match the mechanism to the use case. Don't vector-search what a file path lookup handles. |
| LangChain/LangGraph memory | Framework-level memory primitives tied to their orchestration layer | Anamnesis is orchestration-agnostic. Works with LangGraph, works without it. The memory layer doesn't care what runs the agent. |
| RAG-over-everything | Embed everything, retrieve by similarity, hope for the best | Compilation over retrieval. Do the hard work at write time so read time is trivial. A curated wiki beats a vector store. |

The positioning statement: **"Your agent's memory should belong to you, not your AI provider. Anamnesis is an open framework for building agent memory systems that are portable, inspectable, and curated by humans -- not hoarded by platforms."**

---

## Path Forward

### Phase 1: Build and Validate (Now -- Month 3)

- Build the Anamnesis Python library (per construction doc build order)
- Apply it to Atlas first (Circle 1 + Circle 2, immediate value)
- Apply it to the-agency (learned knowledge wiki for voice agents)
- Validate compilation quality on real transcripts
- Validate reconciliation UX (does the business owner actually review?)

### Phase 2: Publish (Month 3-4)

- Clean the library API, write documentation
- Publish to GitHub with MIT license
- Write the first 2-3 blog posts
- Announce on Hacker News, dev.to, LinkedIn, X
- Link from the-agency marketing site ("powered by Anamnesis")

### Phase 3: Grow (Month 4-12)

- Onboard first paying tenants for the-agency in Kingsport/Johnson City market
- Iterate on the framework based on real-world usage
- Accept community contributions to the open source library
- Publish additional content as new concepts are validated
- Explore chamber of commerce partnership for tenant acquisition

### Phase 4: Expand (Month 12+)

- Apply Anamnesis to Selah (theological knowledge base, behavioral mining for study habits)
- Explore consulting opportunities for enterprise Anamnesis implementations
- Evaluate the vertical bolus marketplace based on tenant density
- Consider Anamnesis as a standalone brand if adoption warrants it

---

## The Moat

The moat is not the code. Open source code is copyable by definition. The moat is the combination of:

1. **The framework's intellectual depth.** The five-circle model, the triage questions, the clinical analogies -- these took years of cross-domain experience to produce. A developer can copy the code. They can't copy the twenty years of clinical informatics that informed the architecture.

2. **Front-end curation as a design principle.** Most competitors optimize for collection. Anamnesis optimizes for curation. This is a philosophical difference that permeates every design decision and is hard to replicate by copying code alone.

3. **First-mover on the counter-narrative.** The "your memory should be yours" position is open for the taking. Whoever articulates it clearly and backs it with a working implementation gets to own that space. Proprietary memory systems will always exist. The open alternative needs a name and a champion.

4. **Domain crossover credibility.** A physician-informaticist building AI memory systems from clinical principles is a unique positioning that no pure software developer can replicate. The medication reconciliation model isn't an analogy you googled -- it's a process you've practiced for twenty years. That authenticity is the moat.
