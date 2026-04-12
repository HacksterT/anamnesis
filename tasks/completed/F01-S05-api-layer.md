---
id: F01-S05
feature: F01
title: REST API Layer
priority: Must-Have
status: done
created: 2026-04-12
type: software
---

# F01-S05: REST API Layer

**Feature:** F01 — Circle 1 & Circle 2 Core
**Priority:** Must-Have

## Summary

Implement a thin FastAPI wrapper around the Anamnesis library so any LLM system can access knowledge injection and bolus management via HTTP. This is what makes Anamnesis LLM-agnostic — a Claude agent, a local Gemma 4 model, an OpenAI assistant, or any custom system can call `GET /v1/knowledge/injection` and receive the assembled `anamnesis.md` as plain text. The API includes a dedicated `retrieve_knowledge` endpoint that serves as the HTTP implementation of the tool contract defined in S03. Every endpoint delegates to `KnowledgeFramework` methods. Library-first consumers (Python imports) skip this layer entirely.

## Acceptance Criteria

- [x] `GET /v1/knowledge/injection` returns the assembled `anamnesis.md` as `text/markdown` with correct `<knowledge>` wrapper
- [x] `GET /v1/knowledge/injection/metrics` returns token counts, budget utilization, and bolus statistics as JSON
- [x] `GET /v1/knowledge/boluses` returns a JSON list of bolus metadata; `?active_only=true` filters to active only
- [x] `GET /v1/knowledge/boluses/{id}` returns bolus content and metadata in a JSON envelope
- [x] `POST /v1/knowledge/boluses` creates a new bolus (JSON body with `id`, `title`, `summary`, `content`, `render`, `priority`, `tags`) — returns 201
- [x] `PUT /v1/knowledge/boluses/{id}` updates bolus content
- [x] `DELETE /v1/knowledge/boluses/{id}` deletes a bolus
- [x] `PATCH /v1/knowledge/boluses/{id}/activate` and `/deactivate` toggle activation state
- [x] `GET /v1/knowledge/retrieve/{id}` returns bolus content as `text/markdown` (the `retrieve_knowledge` tool endpoint)
- [x] Optional API key auth: if `config.api_key` is set, all `/v1/` routes require `Authorization: Bearer {key}`; health and docs endpoints skip auth
- [x] `GET /v1/health` returns `{"status": "ok", "version": "0.1.0"}`
- [x] Server starts with `anamnesis serve` CLI command or `uvicorn anamnesis.api.server:app`
- [x] CLI entry points: `anamnesis serve`, `anamnesis assemble`, `anamnesis validate`, `anamnesis metrics`
- [x] API returns appropriate HTTP status codes: 200, 201, 404, 409 (duplicate), 422 (validation error)
- [x] Config loading from YAML file (explicit path, `ANAMNESIS_CONFIG` env var, or default filenames)

## Tasks

### Backend

- [x] Implement the FastAPI app in `src/anamnesis/api/server.py`:
  - App factory: `create_app(config: KnowledgeConfig) -> FastAPI`
  - Pydantic request/response models: `BolusCreate`, `BolusUpdate`, `HealthResponse`
  - All endpoints delegate to `KnowledgeFramework` methods

- [x] Implement injection endpoints:
  ```
  GET  /v1/knowledge/injection          -> text/markdown
  GET  /v1/knowledge/injection/metrics  -> application/json
  ```

- [x] Implement bolus CRUD endpoints:
  ```
  GET    /v1/knowledge/boluses              -> JSON list of metadata
  GET    /v1/knowledge/boluses/{id}         -> JSON envelope (id, metadata, content)
  POST   /v1/knowledge/boluses              -> 201 Created
  PUT    /v1/knowledge/boluses/{id}         -> 200 OK
  DELETE /v1/knowledge/boluses/{id}         -> 200 OK or 404
  PATCH  /v1/knowledge/boluses/{id}/activate    -> 200 OK
  PATCH  /v1/knowledge/boluses/{id}/deactivate  -> 200 OK
  ```

- [x] Implement `retrieve_knowledge` tool endpoint:
  ```
  GET  /v1/knowledge/retrieve/{id}      -> text/markdown (bolus content)
  ```
  This is the HTTP implementation of the `retrieve_knowledge` tool contract from S03. Agent frameworks that use HTTP tools (MCP over HTTP, OpenAI function calling with URL actions) point to this endpoint.

- [x] Implement optional API key middleware — checks `Authorization: Bearer {key}` on all `/v1/` routes except health and docs

- [x] Implement config loading in `src/anamnesis/api/config_loader.py`:
  - Resolution: explicit path → `ANAMNESIS_CONFIG` env var → default filenames in cwd
  - Supports YAML and JSON
  - Example `anamnesis.yaml`:
    ```yaml
    circle1_path: ./knowledge/anamnesis.md
    circle2_root: ./knowledge/boluses/
    circle1_max_tokens: 4000
    api_port: 8741
    ```

- [x] Implement CLI in `src/anamnesis/cli.py`:
  - `anamnesis serve` — starts FastAPI/uvicorn with config loading
  - `anamnesis assemble` — assembles and writes `anamnesis.md`
  - `anamnesis validate` — validates injection against schema
  - `anamnesis metrics [--json]` — shows token counts and budget utilization
  - Wired via `[project.scripts]` in pyproject.toml

- [x] Add OpenAPI metadata for auto-generated docs at `/docs`

- [x] Add convenience `Dockerfile` at repo root

### Dependencies

- [x] FastAPI and Uvicorn in `[project.optional-dependencies] api`
- [x] httpx in `[project.optional-dependencies] dev` (for FastAPI TestClient)

### Testing & Verification

- [x] Write test: health endpoint returns 200 with version
- [x] Write test: `GET /v1/knowledge/injection` returns valid markdown
- [x] Write test: injection includes active boluses, excludes inactive
- [x] Write test: injection metrics returns correct counts
- [x] Write test: bolus list with active_only filter
- [x] Write test: bolus GET returns JSON envelope with content and metadata
- [x] Write test: bolus POST/GET/PUT/DELETE lifecycle
- [x] Write test: 404 on nonexistent bolus
- [x] Write test: 409 on duplicate bolus creation
- [x] Write test: activate/deactivate toggle via PATCH
- [x] Write test: `retrieve_knowledge` endpoint returns bolus content
- [x] Write test: API key auth enforced when configured, skipped when not
- [x] Local Testing: `pytest tests/` passes — 94 tests total
- [x] Manual Testing: CHECKPOINT — Start server, call endpoints with curl

### Git

- [ ] Commit, fetch/rebase, push

## Technical Notes

- **Library-first.** Every API endpoint is a thin wrapper: parse request → call `KnowledgeFramework` method → format response. No business logic in the API layer.
- **Content negotiation.** Injection and retrieve endpoints return `text/markdown`. Bolus list and metrics return `application/json`. Individual bolus GET returns a JSON envelope with both metadata and content.
- **The `retrieve_knowledge` endpoint** (`GET /v1/knowledge/retrieve/{id}`) is the HTTP implementation of the tool contract. For agent frameworks that support URL-based tools, this is the endpoint they point to. For Python-native agents, they call `kf.retrieve()` directly.
- **Config file format.** YAML preferred for human authoring. JSON supported for programmatic generation. No `identity_source` or `constraints_source` fields — all content comes from boluses.
- **Port 8741.** Default port chosen to avoid conflicts with common dev servers. Configurable via config or `--port` flag.
- **No WebSocket or streaming.** The injection document is small (< 6K tokens ≈ < 25KB). Streaming is unnecessary.
- **CORS not enabled by default.** Will be needed for S07 (web dashboard). Can be added via middleware config.

## Blockers

- F01-S02 (Bolus System) — depends on bolus CRUD operations.
- F01-S04 (Injection Assembly) — depends on `get_injection()` and `get_injection_metrics()`.
