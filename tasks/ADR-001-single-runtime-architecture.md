---
title: "ADR-001: Single LangGraph Runtime with Anamnesis Knowledge Layer"
date: 2026-04-12
status: accepted
feature: cross-cutting
---

# ADR-001: Single LangGraph Runtime with Anamnesis Knowledge Layer

## Context

The current personal agent stack has three separate systems:
- **Atlas** (TypeScript) — personal assistant with three personas (CTO, assistant, researcher), skill system, tool calls, auto-memory
- **Selah-personal** (Python, Gemma 4) — theological knowledge base, new, minimal
- **Anamnesis** (Python) — knowledge management framework with REST API, dashboard, CLI

This creates architectural fragmentation: two languages, separate memory systems, HTTP bridges between Python and TypeScript, no shared runtime, and tool duplication.

Meanwhile, **the-agency** repo already contains a working LangGraph multi-agent runtime with supervisor routing, subgraph-based skills, and tool registration — the exact architecture needed for the personal stack.

## Decision

Consolidate into a **single LangGraph runtime** (forked from the-agency) with three C-suite agents. Anamnesis is imported as a library, not called over HTTP. Atlas is deprecated after migration.

### Architecture

```
Single LangGraph Runtime (Python)
    │
    ├── Supervisor (intent routing)
    │
    ├── CMO — Chief Marketing Officer
    │     Skills (subgraphs): content-creation, social-media, analytics, brand-voice
    │
    ├── CTO — Chief Technical Officer
    │     Skills (subgraphs): deep-research, code-review, infrastructure, deployment
    │
    └── CPO — Chief Pastoral Officer (Selah-personal merged)
          Skills (subgraphs): scripture-search, commentary-lookup, study-guide, sermon-prep
    
Knowledge layer:
    └── anamnesis (library import, same process)
          ├── Per-agent injection: kf.get_injection(agent="cmo"|"cto"|"cpo")
          ├── Per-agent recency: _recency-cmo, _recency-cto, _recency-cpo
          ├── Shared bolus library: knowledge/boluses/
          ├── Per-agent activation profiles
          └── Shared episode capture: Circle 4 SQLite

Dashboard:
    └── FastAPI mounted in the same process
          ├── Serves the SvelteKit dashboard
          └── Reads from the same KnowledgeFramework instance
```

### Key principles

- **Skills are subgraphs.** Each skill is a LangGraph subgraph that encapsulates its tools. The supervisor and agent nodes see skill names, never individual tools. This is the transport layer inversion from the Anamnesis framework (Section 9.2).

- **Tools are registered at runtime.** Tool scripts live in the repo. Subgraphs register their tools when the graph is built. No static tool manifests in the LLM context.

- **Anamnesis is a library, not a service.** The LangGraph runtime imports `KnowledgeFramework` directly. No HTTP API for agent ↔ knowledge communication. The dashboard API is the only HTTP surface, served from the same process.

- **One process, one database.** The LangGraph runtime, the knowledge framework, and the dashboard API share a single process. One `anamnesis.db` for episodes and curation. One `knowledge/boluses/` directory. No inter-process coordination.

- **Per-agent injection.** Each agent node calls `kf.get_injection(agent="cto")` and gets a tailored injection with its identity, activated boluses, skill manifest, recency context, and constraints. The supervisor gets a routing-focused injection (agent summaries, not full knowledge).

## Why

- **One language.** Python everywhere. No TypeScript ↔ Python bridge. No HTTP overhead for what should be function calls.
- **Proven runtime.** The-agency already has LangGraph supervisor routing, subgraph skills, and tool registration working. Not building from scratch.
- **Token efficiency.** Skills as subgraphs means the LLM in each agent node only sees its own skill set, not all tools from all agents. The supervisor sees agent capabilities, not tool-level detail.
- **Shared knowledge.** All three agents read from and write to the same Anamnesis knowledge base. CTO's deep-research findings are available to CMO for content creation. CPO's sermon research informs CTO's understanding of the user's interests. Cross-agent knowledge flows through Circles 2-4 naturally.
- **Single deployment.** One process to start, one process to monitor, one process to restart. The dashboard is embedded, not a separate service.

## Alternatives Considered

### Keep Atlas (TypeScript) + Anamnesis API + Selah separate
- Pro: No migration effort. Atlas works today.
- Con: Two languages, HTTP bridge, fragmented memory, tool duplication, three processes.
- Rejected because the architectural debt compounds with every new feature.

### Migrate Atlas to Python but keep it separate from Selah
- Pro: Unifies language, keeps agents independent.
- Con: Still multiple processes, still need HTTP between agents and Anamnesis, no shared runtime benefits.
- Rejected because LangGraph's value is the shared runtime.

### Use Anthropic Managed Agents instead of LangGraph
- Pro: Anthropic handles the runtime.
- Con: Less control over tool registration, subgraph architecture, and local model integration (CPO needs Gemma 4 option). May be the right long-term path but premature today.
- Deferred for evaluation once Managed Agents matures.

## Consequences

- **Atlas is deprecated.** No new features. Existing functionality is migrated to LangGraph nodes. Atlas stays running until cutover is complete.
- **The-agency repo becomes the foundation.** Fork or adapt its LangGraph runtime for the personal stack.
- **Anamnesis API server is not needed for personal use.** The library import path is primary. The API remains available for external consumers (Selah multi-tenant, future integrations).
- **F03-S01/S02 (agent profiles + injection routing) is a prerequisite.** Per-agent injection must work before the three C-suite agents can get tailored knowledge.
- **The Atlas integration PRD (Phase A) is still valid** as an interim step if Atlas needs Anamnesis before the LangGraph migration is complete. Phase B (transport layer inversion via HTTP) is superseded by this ADR — the inversion happens at the library/subgraph level instead.

## Selah External (Multi-Tenant) — Separate Concern

This ADR applies to the personal stack only. Selah for external pastors remains a separate deployment:
- Selah gateway imports Anamnesis as a library
- Per-tenant `KnowledgeFramework` instances with isolated knowledge dirs
- Gemma 4 (local) as CompletionProvider
- Shared skill subgraphs across tenants
- Its own dashboard or a tenant-aware Anamnesis dashboard
- No connection to the personal LangGraph runtime

The personal CPO node and external Selah share skill definitions and Anamnesis as a library, but run in completely separate processes with separate knowledge.

---

*Accepted: 2026-04-12*
