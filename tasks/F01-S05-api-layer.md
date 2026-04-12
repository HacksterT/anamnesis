---
id: F01-S05
feature: F01
title: REST API Layer
priority: Must-Have
status: backlog
created: 2026-04-12
type: software
---

# F01-S05: REST API Layer

**Feature:** F01 — Circle 1 & Circle 2 Core
**Priority:** Must-Have

## Summary

Implement a thin FastAPI wrapper around the Anamnesis library so any LLM system can access the knowledge injection and bolus management via HTTP. This is what makes Anamnesis LLM-agnostic — a Claude agent, a Gemini voice bot, an OpenAI assistant, or any custom system can call `GET /v1/knowledge/injection` and receive the assembled `anamnesis.md` as plain text. The API is a skin over the library, not a separate product. Every endpoint delegates to `KnowledgeFramework` methods. Library-first consumers (Python imports) skip this layer entirely.

## Acceptance Criteria

- [ ] `GET /v1/knowledge/injection` returns the assembled `anamnesis.md` as `text/markdown` with correct `<knowledge>` wrapper
- [ ] `GET /v1/knowledge/injection/metrics` returns token counts, budget utilization, and section breakdown as JSON
- [ ] `GET /v1/knowledge/boluses` returns a JSON list of bolus metadata (all boluses); `?active_only=true` filters to active only
- [ ] `GET /v1/knowledge/boluses/{bolus_id}` returns bolus content as `text/markdown` and metadata in response headers or a JSON envelope
- [ ] `POST /v1/knowledge/boluses` creates a new bolus (accepts JSON body with `id`, `title`, `summary`, `tags`, `content`)
- [ ] `PUT /v1/knowledge/boluses/{bolus_id}` updates an existing bolus
- [ ] `DELETE /v1/knowledge/boluses/{bolus_id}` deletes a bolus
- [ ] `PATCH /v1/knowledge/boluses/{bolus_id}/activate` and `/deactivate` toggle the activation state
- [ ] Optional API key auth: if `config.api_key` is set, all requests require `Authorization: Bearer {key}` header; if not set, no auth required
- [ ] `GET /v1/health` returns `{"status": "ok", "version": "0.1.0"}`
- [ ] The server starts with `anamnesis serve` CLI command or `uvicorn anamnesis.api.server:app`
- [ ] API returns appropriate HTTP status codes: 200, 201, 404, 409 (duplicate bolus), 422 (validation error), 500

## Tasks

### Backend

- [ ] Add FastAPI and Uvicorn to `[project.optional-dependencies]` under an `api` group:
  ```toml
  [project.optional-dependencies]
  api = ["fastapi>=0.115", "uvicorn>=0.30"]
  ```

- [ ] Implement the FastAPI app in `src/anamnesis/api/server.py`:
  - App factory: `create_app(config: KnowledgeConfig) -> FastAPI`
  - The app holds a single `KnowledgeFramework` instance initialized from config
  - Config loading: read from environment variable `ANAMNESIS_CONFIG` (path to a YAML/JSON config file) or from default paths

- [ ] Implement injection endpoints:
  ```
  GET  /v1/knowledge/injection          -> text/markdown (the assembled anamnesis.md)
  GET  /v1/knowledge/injection/metrics  -> application/json (token counts, utilization)
  ```

- [ ] Implement bolus CRUD endpoints:
  ```
  GET    /v1/knowledge/boluses              -> JSON list of bolus metadata
  GET    /v1/knowledge/boluses/{id}         -> text/markdown (bolus content) + metadata in JSON envelope
  POST   /v1/knowledge/boluses              -> 201 Created (JSON body: id, title, summary, tags, content)
  PUT    /v1/knowledge/boluses/{id}         -> 200 OK (update content and/or metadata)
  DELETE /v1/knowledge/boluses/{id}         -> 200 OK or 404 Not Found
  PATCH  /v1/knowledge/boluses/{id}/activate    -> 200 OK (set active: true)
  PATCH  /v1/knowledge/boluses/{id}/deactivate  -> 200 OK (set active: false)
  ```

- [ ] Implement optional API key middleware:
  - If `config.api_key` is set, require `Authorization: Bearer {key}` on all `/v1/` routes
  - If not set, skip auth entirely (local development mode)
  - Return 401 Unauthorized with clear error message on missing/invalid key

- [ ] Implement config loading:
  - `ANAMNESIS_CONFIG` env var points to a YAML or JSON file
  - Fallback: look for `anamnesis.yaml` or `anamnesis.json` in current directory
  - Config file maps to `KnowledgeConfig` fields
  - Example `anamnesis.yaml`:
    ```yaml
    circle1_path: ./knowledge/anamnesis.md
    circle2_root: ./knowledge/boluses/
    circle1_max_tokens: 4000
    identity_source: ./knowledge/identity.md
    constraints_source: ./knowledge/constraints.md
    api_port: 8741
    ```

- [ ] Implement CLI entry point:
  - `anamnesis serve` — starts the API server (reads config, creates app, runs uvicorn)
  - `anamnesis assemble` — runs the assembler once and writes `anamnesis.md` (no server)
  - `anamnesis validate` — validates config and bolus structure without serving
  - Add CLI via `[project.scripts]` in pyproject.toml using click or argparse

- [ ] Implement `GET /v1/health` endpoint (no auth required)

- [ ] Add OpenAPI metadata (title: "Anamnesis Knowledge API", description, version) for auto-generated docs at `/docs`

- [ ] Add a convenience `Dockerfile` at the repo root:
  ```dockerfile
  FROM python:3.11-slim
  COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
  WORKDIR /app
  COPY . .
  RUN uv sync --extra api --no-dev
  EXPOSE 8741
  CMD ["uv", "run", "anamnesis", "serve"]
  ```
  This is a deployment convenience, not a development requirement. Local workflow remains `uv sync && uv run anamnesis serve`.

### Dependencies (if new packages added)

- [ ] Audit FastAPI: check version, known advisories
- [ ] Audit Uvicorn: check version, known advisories
- [ ] Audit PyYAML (for config loading): check version, known advisories
- [ ] Pin exact versions in lock file
- [ ] Document new dependencies and versions in Technical Notes

### Testing & Verification

- [ ] Write test: `GET /v1/knowledge/injection` returns valid markdown with `<knowledge>` wrapper
- [ ] Write test: `GET /v1/knowledge/boluses` returns JSON list; filtered by `active_only` query param
- [ ] Write test: POST/GET/PUT/DELETE lifecycle on a bolus via API
- [ ] Write test: activate/deactivate toggle via PATCH endpoints
- [ ] Write test: 404 on nonexistent bolus ID
- [ ] Write test: 409 on duplicate bolus creation
- [ ] Write test: API key auth enforced when configured; requests pass without auth when not configured
- [ ] Write test: health endpoint returns 200 with version
- [ ] Use FastAPI TestClient (no actual server process needed for tests)
- [ ] Local Testing: `pytest tests/` passes, all acceptance criteria verified
- [ ] Manual Testing: CHECKPOINT — Start server with `anamnesis serve`, call endpoints with curl, verify injection output and bolus CRUD

### Git

- [ ] Commit, fetch/rebase, push

## Technical Notes

- **Library-first.** Every API endpoint is a thin wrapper: parse request → call `KnowledgeFramework` method → format response. No business logic in the API layer. If a consumer prefers Python imports over HTTP, they use the library directly and this layer doesn't exist for them.
- **Content negotiation.** The injection endpoint returns `text/markdown` because the consumer is an LLM system that will inject the content as-is. The bolus list endpoint returns `application/json` because the consumer is likely a dashboard or management tool. Individual bolus retrieval returns content in a JSON envelope: `{"id": "...", "metadata": {...}, "content": "..."}` so the consumer gets both metadata and markdown body in one call.
- **Config file format.** YAML is preferred for human authoring (matches the bolus frontmatter format). JSON is supported for programmatic generation. The config loader tries YAML first, falls back to JSON.
- **Port 8741.** Default port chosen to avoid conflicts with common development servers (3000, 5000, 8000, 8080). Configurable via `api_port`.
- **No WebSocket or streaming.** The injection endpoint returns the full document in one response. The document is small (< 6K tokens ≈ < 25KB). Streaming is unnecessary and adds complexity.
- **CORS.** Not enabled by default. If a future web-based curation UI needs to call the API from a browser, CORS middleware can be added via config. Phase 1 assumes local or server-to-server usage.

## Blockers

- F01-S01 (Project Scaffolding) — depends on package structure and `KnowledgeConfig`.
- F01-S02 (Bolus System) — depends on bolus CRUD operations.
- F01-S04 (Injection Assembly) — depends on `get_injection()` and `get_injection_metrics()`.
