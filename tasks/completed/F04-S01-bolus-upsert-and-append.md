---
id: F04-S01
feature: F04
title: Bolus Upsert & Append
priority: Must-Have
status: done
created: 2026-04-12
type: software
---

# F04-S01: Bolus Upsert & Append

**Feature:** F04 — External Content Intake
**Priority:** Must-Have

## Summary

Add upsert and append semantics to the bolus system so external agents can push synthesized content into a named bolus without managing its existence state. Today, `POST /v1/knowledge/boluses` 409s if the bolus already exists and `PUT /v1/knowledge/boluses/{id}` 404s if it doesn't — a calling agent must do a GET first to decide which to use. This story adds `kf.upsert_bolus()` (create-or-replace) and `kf.append_bolus()` (add to existing), wires them into the API and CLI, and changes `PUT /v1/knowledge/boluses/{id}` to upsert semantics so a single call handles both the cold-start (new bolus) and incremental-update (existing bolus) cases. The canonical use case: Ezra processes a YouTube transcript, synthesizes a guide, and calls `PUT /v1/knowledge/boluses/ai-memory-research` — the bolus is created on the first call and its content is replaced with each re-synthesis. For incremental accumulation, `POST /v1/knowledge/boluses/ai-memory-research/append` adds a new section without touching existing content.

## Acceptance Criteria

- [x] `kf.upsert_bolus("ai-memory-research", content)` creates the bolus if it doesn't exist, replaces content if it does, preserving existing metadata (title, tags, priority) on update
- [x] `kf.upsert_bolus()` accepts optional `title`, `summary`, `tags`, `render`, `priority` for the create case; these are ignored if the bolus already exists
- [x] `kf.append_bolus("ai-memory-research", new_section)` appends content to an existing bolus with a `\n\n---\n\n` separator; raises `KeyError` if bolus doesn't exist
- [x] `kf.append_bolus()` accepts an optional `separator` argument to override the default
- [x] `PUT /v1/knowledge/boluses/{id}` upserts: 200 with `status: updated` if existed, 201 with `status: created` if new
- [x] `PUT /v1/knowledge/boluses/{id}` body accepts: `content` (required), `title`, `summary`, `tags`, `render`, `priority` (all optional, used only on create)
- [x] `POST /v1/knowledge/boluses/{id}/append` appends content; 200 on success, 404 if bolus not found
- [x] `POST /v1/knowledge/boluses/{id}/append` accepts optional `separator` in the request body
- [x] `anamnesis bolus append <id> [--file FILE | --content TEXT] [--separator SEP]` works at CLI
- [x] All existing bolus tests continue to pass (no regressions)

## Tasks

### Backend

- [x] Add `append()` method to `MarkdownBolusStore`:
  - Read existing content via `read_full()`
  - Concatenate with separator: `existing + separator + new_content`
  - Write back with `write()` preserving metadata (`updated` timestamp refreshed)
  - Raise `KeyError` if bolus doesn't exist
- [x] Add `kf.upsert_bolus(bolus_id, content, *, title=None, summary=None, render=None, priority=None, tags=None)` to `KnowledgeFramework`:
  - If bolus exists: call `update_bolus(bolus_id, content)` (preserves metadata)
  - If not: call `create_bolus(bolus_id, content, ...)` with provided or default metadata
  - Return `"created"` or `"updated"` to indicate which path was taken
- [x] Add `kf.append_bolus(bolus_id, content, separator="\n\n---\n\n")` to `KnowledgeFramework`:
  - Delegates to `self._store.append(bolus_id, content, separator)`
- [x] Add `BolusUpsert` Pydantic model to API:
  ```python
  class BolusUpsert(BaseModel):
      content: str
      title: str | None = None
      summary: str | None = None
      render: str = "reference"
      priority: int = 50
      tags: list[str] = []
  ```
- [x] Add `BolusAppend` Pydantic model:
  ```python
  class BolusAppend(BaseModel):
      content: str
      separator: str = "\n\n---\n\n"
  ```
- [x] Change `PUT /v1/knowledge/boluses/{bolus_id}` to use `BolusUpsert` and call `kf.upsert_bolus()`:
  - Return 201 on create, 200 on update
- [x] Add `POST /v1/knowledge/boluses/{bolus_id}/append` endpoint calling `kf.append_bolus()`

### CLI

- [x] Add `anamnesis bolus append <id>` subparser with `--file`, `--content`, `--separator` flags
- [x] Implement `_cmd_bolus` dispatch for `append`: read content from `--file` or `--content` (stdin fallback optional), call `kf.append_bolus()`

### Testing & Verification

- [x] Write test: `upsert_bolus` creates when bolus doesn't exist
- [x] Write test: `upsert_bolus` replaces content when bolus exists, metadata preserved
- [x] Write test: `upsert_bolus` returns `"created"` / `"updated"` correctly
- [x] Write test: `append_bolus` appends with default separator
- [x] Write test: `append_bolus` appends with custom separator
- [x] Write test: `append_bolus` raises `KeyError` on missing bolus
- [x] Write test: `PUT /v1/knowledge/boluses/{id}` returns 201 on create, 200 on update
- [x] Write test: `POST /v1/knowledge/boluses/{id}/append` returns 200, 404 on missing
- [x] Write test: CLI `anamnesis bolus append` works with `--file`
- [x] Local Testing: `pytest tests/` passes — 212 tests passing (195 pre-existing + 17 new)
- [x] Manual Testing: CHECKPOINT — Notify user to verify upsert and append with a real bolus

### Git

- [ ] Commit, fetch/rebase, push

## Technical Notes

- **Breaking change to PUT semantics.** The existing `PUT /v1/knowledge/boluses/{id}` returned 404 if the bolus didn't exist. Changed to upsert. The pre-existing `test_update_bolus_not_found` test was updated to assert 201 instead of 404 — this was the only consumer of the old behavior.
- **Metadata preservation on upsert-update.** When the bolus already exists, `upsert_bolus()` calls `update_bolus()` which reads existing metadata and rewrites. Title, tags, priority, render mode are all preserved. Only `content` and `updated` date change. Metadata supplied in the upsert request is silently ignored for the update case.
- **Append separator choice.** Default `\n\n---\n\n` renders as a horizontal rule in markdown, visually separating accumulated sections. Configurable per-call via `separator` argument — resolved open design decision.
- **Upsert metadata on create.** Metadata fields (`title`, `summary`, `tags`, `render`, `priority`) are accepted in the `PUT` request body and used only if the bolus is being created. Resolved open design decision.
- **No merge/diff.** Upsert replaces content wholesale. For incremental accumulation, use `append`. Anamnesis does not attempt to merge or diff content.

## Blockers

None.
