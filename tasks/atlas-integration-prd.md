---
id: ATLAS-INT
title: Atlas ↔ Anamnesis Integration
status: draft
created: 2026-04-12
type: software
for: Atlas repo
---

# Atlas ↔ Anamnesis Integration

**Repo:** Atlas (TypeScript)
**Depends on:** Anamnesis REST API running at `localhost:8741`

## Overview

**Problem:** Atlas currently manages memory through Claude Code's auto-memory system — scattered markdown files in `~/.claude/` with no structure, no curation, and no shared access. When Anamnesis replaces this, Atlas needs a way to consume knowledge injection, retrieve boluses on demand, and capture conversation episodes — all via HTTP from TypeScript.

**Goal:** A TypeScript client for the Anamnesis API that lets Atlas: (1) fetch its assembled knowledge injection at session start, (2) retrieve full bolus content mid-conversation via the `retrieve_knowledge` tool, and (3) capture conversation turns and end sessions so the recency pipeline keeps working.

## Architecture

```
┌─────────────────────┐         HTTP          ┌──────────────────────┐
│       Atlas          │ ──────────────────── │   Anamnesis API      │
│   (TypeScript)       │                       │   localhost:8741     │
│                      │  GET /injection       │                      │
│  System prompt ◄─────│◄─────────────────────│  anamnesis.md        │
│                      │                       │                      │
│  Tool: retrieve ─────│──────────────────────►│  GET /retrieve/{id}  │
│  knowledge           │                       │                      │
│                      │  POST /episodes/turn  │                      │
│  Conversation ───────│──────────────────────►│  SQLite episodes     │
│  capture             │  POST /episodes/end   │                      │
└─────────────────────┘                       └──────────────────────┘
```

Atlas and Selah-personal both talk to the same Anamnesis API instance. Same knowledge base, same boluses, same episodes. The API is the shared interface — Atlas uses it because it's TypeScript and can't import the Python library directly.

## Deliverables

### 1. Anamnesis TypeScript Client

A small, typed HTTP client for the Anamnesis API. Could live in Atlas's repo as a utility module or as a standalone package.

```typescript
// anamnesis-client.ts

export class AnamnesisClient {
  constructor(private baseUrl: string = 'http://localhost:8741') {}

  /** Fetch the assembled anamnesis.md for system prompt injection. */
  async getInjection(): Promise<string>

  /** Retrieve full bolus content by ID (the retrieve_knowledge tool). */
  async retrieveKnowledge(bolusId: string): Promise<string>

  /** Capture a conversation turn. */
  async captureTurn(role: string, content: string): Promise<void>

  /** End the current session. Triggers recency pipeline. */
  async endSession(summary?: string, agent?: string): Promise<string | null>

  /** Health check — verify API is reachable. */
  async health(): Promise<{ status: string; version: string }>
}
```

**Design notes:**
- Zero dependencies beyond `fetch` (native in Node 18+).
- All methods are async. Errors throw with status code and detail message.
- The `agent` parameter on `endSession` should be `"atlas"` — this tags the episode so Anamnesis knows which agent captured it.
- No bolus CRUD methods needed in the client. Atlas doesn't manage boluses — the human does that through the dashboard. Atlas only reads and captures.

### 2. System Prompt Integration

Atlas currently loads its system prompt from CLAUDE.md or similar. Replace that with an Anamnesis injection call at session start.

```typescript
// Before each conversation or session
const client = new AnamnesisClient();
const injection = await client.getInjection();

// Inject into the LLM call
const response = await claude.messages.create({
  system: injection,  // anamnesis.md content goes here
  messages: [...],
});
```

**Fallback behavior:** If the Anamnesis API is unreachable, Atlas should fall back to a cached version of the injection (last known good `anamnesis.md`) or a minimal hardcoded system prompt. The API being down shouldn't break Atlas.

### 3. Tool Registration: `retrieve_knowledge`

Register `retrieve_knowledge` as a tool that Atlas's LLM can call. When the LLM sees a bolus pointer in the injection manifest (e.g., `-> \`infrastructure\``) and decides it needs the full content, it calls this tool.

```typescript
// Tool definition for Claude tool_use
{
  name: "retrieve_knowledge",
  description: "Retrieve the full content of a knowledge bolus by ID. Use when you need details beyond what the summary in your knowledge prompt provides.",
  input_schema: {
    type: "object",
    properties: {
      bolus_id: {
        type: "string",
        description: "The bolus identifier from the knowledge manifest (e.g. 'infrastructure')"
      }
    },
    required: ["bolus_id"]
  }
}
```

**Tool handler:**
```typescript
async function handleRetrieveKnowledge(bolusId: string): Promise<string> {
  const client = new AnamnesisClient();
  return await client.retrieveKnowledge(bolusId);
}
```

The tool result (bolus content) goes back into the conversation as a tool_result message. The LLM reads it and continues. One retrieval per bolus per conversation — once it's in context, subsequent messages can reference it.

### 4. Conversation Capture

Atlas should capture conversation turns and end sessions so the recency pipeline works. This gives Atlas (and any other agent reading the same knowledge) awareness of what happened in the last session.

```typescript
// During conversation — after each user message and assistant response
await client.captureTurn("user", userMessage);
await client.captureTurn("assistant", assistantResponse);

// When the conversation ends
await client.endSession(
  "Worked on Anamnesis integration. Decided on TypeScript client approach.",
  "atlas"  // agent name for episode attribution
);
```

**When to call `endSession`:**
- When the user explicitly ends the session
- On a timeout/idle trigger
- On process shutdown (graceful)

**What happens on `endSession`:** The API writes the episode to SQLite, runs the recency pipeline (summarizes the session into the `_recency` bolus), and runs episode retention cleanup. The next `getInjection()` call will include the recency summary.

### 5. Existing Memory Migration

Atlas has existing memories in `~/.claude/projects/*/memory/`. These should be migrated to Anamnesis boluses. This is a one-time operation.

**Approach:** Either:
- (a) A script in Atlas that reads memory files and calls `POST /v1/knowledge/boluses` for each
- (b) The `anamnesis migrate` CLI command (planned in Anamnesis but not yet built)
- (c) Manual curation — read each memory, decide if it's still relevant, create boluses via the dashboard

Option (c) is recommended for Atlas specifically because the existing memories are ad-hoc and many may be stale. A human review pass during migration ensures only current, relevant knowledge enters the system.

## Acceptance Criteria

- [ ] `AnamnesisClient` class with typed methods for injection, retrieval, capture, and health
- [ ] Atlas loads system prompt from `client.getInjection()` at session start
- [ ] Fallback to cached injection if API is unreachable
- [ ] `retrieve_knowledge` registered as a Claude tool with proper handler
- [ ] Conversation turns captured via `client.captureTurn()` during sessions
- [ ] `client.endSession("atlas")` called on session end
- [ ] Health check on Atlas startup to verify Anamnesis API connectivity
- [ ] Existing Atlas memories reviewed and migrated to boluses (manual)

## Non-Goals

- Atlas does not manage boluses. No create/update/delete from Atlas. The human manages knowledge through the dashboard.
- Atlas does not run the Anamnesis API. The API runs independently (`anamnesis serve` or via `start.sh`).
- No changes to the Anamnesis codebase. Everything Atlas needs is already exposed at `/v1/`.
- No TypeScript package published to npm at this stage. The client lives in Atlas's repo.

## Technical Notes

- **Base URL configuration.** Default `localhost:8741` works for development on the Mac Mini. If Atlas ever runs on a different machine, the URL needs to be configurable (env var or config file).
- **API key auth.** If `api_key` is configured in Anamnesis, Atlas needs to send `Authorization: Bearer {key}` on every request. The client constructor should accept an optional API key.
- **Error handling.** The Anamnesis API returns standard HTTP codes: 200/201 for success, 404 for not found, 422 for validation errors, 500 for server errors. The client should map these to typed errors.
- **No WebSocket.** All communication is request/response HTTP. No streaming, no push notifications. Atlas polls or calls on demand.
- **Concurrency.** Multiple Atlas sessions could be active simultaneously (multiple terminal windows). Each session's `captureTurn` calls go to the same API. Episodes are identified by session, so concurrent capture is safe as long as each session calls `endSession` when done. Note: the current `KnowledgeFramework` holds one in-memory session at a time — if Atlas has multiple concurrent sessions hitting the API, only the last one's turns will be in the recency bolus. This is acceptable for personal use; multi-session support would need session IDs in the API.

## Blockers

- Anamnesis API must be running. Atlas should verify on startup and warn if unreachable.
- Existing Atlas memories should be reviewed before migration to avoid importing stale knowledge.
