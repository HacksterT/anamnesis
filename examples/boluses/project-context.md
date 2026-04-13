---
id: project-context
title: Project Context
active: true
render: reference
priority: 20
summary: Active project goals, architecture decisions, and current sprint focus.
tags:
  - project
created: '2024-01-01'
updated: '2024-01-01'
---

**Project:** Acme API v2 — rebuild of the legacy monolith as a FastAPI service mesh.

**Architecture decision (2024-03):** Chose event-driven architecture over direct service calls. All inter-service communication goes through the message bus. Rationale: decouples deployment cycles, enables replay for debugging.

**Current focus:** Auth service migration. The legacy JWT validation is in middleware — we're moving it to a dedicated auth service with a local cache to avoid per-request roundtrips.

**Known constraints:** The payments service cannot be taken offline for migration. Must use a strangler-fig pattern. All payment endpoints must remain on v1 schema until Q3.

**Team convention:** PRs require two reviewers. No force-push to main. All API changes require an updated OpenAPI spec before merge.
