---
id: F01-S02
feature: F01
title: Bolus System (Circle 2)
priority: Must-Have
status: done
created: 2026-04-12
type: software
---
# F01-S02: Bolus System (Circle 2)

**Feature:** F01 — Circle 1 & Circle 2 Core
**Priority:** Must-Have

## Summary

Implement the Circle 2 knowledge bolus system — the confirmed knowledge library. Each bolus is a markdown file with YAML frontmatter stored in the Circle 2 root directory. This story delivers full CRUD operations, the activation toggle model (active/inactive per bolus), metadata management, categorical pointer retrieval, and the `MarkdownBolusStore` implementation of the `BolusStore` interface defined in S01. After this story, boluses can be created, read, updated, deleted, listed, filtered by activation state, and retrieved by ID.

## Acceptance Criteria

- [X] `kf.create_bolus("infrastructure", content, tags=["technical"])` creates a markdown file at `{circle2_root}/infrastructure.md` with correct frontmatter
- [X] `kf.read_bolus("infrastructure")` returns the bolus content (body only, not frontmatter)
- [X] `kf.update_bolus("infrastructure", new_content)` updates the body and sets `updated` timestamp in frontmatter
- [X] `kf.delete_bolus("infrastructure")` removes the file and returns True; returns False if not found
- [X] `kf.list_boluses()` returns metadata dicts for all active boluses; `kf.list_boluses(active_only=False)` returns all
- [X] `kf.set_bolus_active("infrastructure", False)` sets the activation toggle in frontmatter; bolus is excluded from `list_boluses()` default call
- [X] `kf.get_bolus_metadata("infrastructure")` returns the full frontmatter as a dict
- [X] Bolus frontmatter schema is validated on write — required fields enforced, unknown fields preserved
- [X] Bolus IDs are slugified (lowercase, hyphens, no spaces or special characters)
- [X] Creating a bolus with an ID that already exists raises a clear error (not silent overwrite)

## Tasks

### Backend

- [X] Define the bolus frontmatter schema:
  ```yaml
  ---
  id: infrastructure                # Required. Unique slug identifier.
  title: Infrastructure             # Required. Human-readable display name.
  active: true                      # Required. Activation toggle.
  render: reference                 # Required. "inline" or "reference".
  priority: 50                      # Optional. Ordering in injection (lower = earlier).
  summary: "Mac Mini M4 Pro, macdevserver (Ubuntu), home network."
                                    # Required. One-line summary.
  tags: [technical, hardware]       # Optional. Free-form categorization.
  created: 2026-04-12               # Required. ISO date. Set on creation.
  updated: 2026-04-12               # Required. ISO date. Updated on every write.
  ---
  ```
- [X] Implement `MarkdownBolusStore` in `bolus/store.py`:
  - `read(bolus_id)` — parse markdown file, return body (content below frontmatter)
  - `write(bolus_id, content, metadata)` — write frontmatter + content to `{circle2_root}/{bolus_id}.md`; set `created`/`updated` timestamps; validate required frontmatter fields
  - `delete(bolus_id)` — remove file, return success boolean
  - `list(active_only=True)` — scan directory, parse frontmatter from all `.md` files, return metadata dicts; filter by `active` field
  - `exists(bolus_id)` — check file existence
  - `get_metadata(bolus_id)` — parse and return frontmatter only
  - `set_active(bolus_id, active)` — read file, update `active` field in frontmatter, rewrite file preserving body
- [X] Implement frontmatter parsing — use a lightweight approach (read YAML between `---` delimiters) rather than adding a heavy dependency. Consider `python-frontmatter` or a simple regex-based parser.
- [X] Implement bolus ID validation — slugify on create, reject invalid characters on read/write
- [X] Wire `KnowledgeFramework` methods: `create_bolus`, `read_bolus`, `update_bolus`, `delete_bolus`, `list_boluses`, `set_bolus_active`, `get_bolus_metadata` — each delegates to `self.bolus_store`
- [X] Implement `retrieve(bolus_id)` on `KnowledgeFramework` — alias for `read_bolus` that follows the framework's categorical pointer pattern (Circle 1 points to bolus ID, agent calls retrieve with that ID)

### Testing & Verification

- [X] Write tests: create/read/update/delete lifecycle, list with active_only filtering, set_active toggle, duplicate ID rejection, invalid ID handling, frontmatter validation, retrieve by categorical pointer
- [X] Test that frontmatter round-trips correctly (write then read preserves all fields including unknown/extra fields)
- [X] Test that bolus files are human-readable markdown (open in a text editor and verify structure)
- [X] Local Testing: `pytest tests/` passes, all acceptance criteria verified
- [X] Manual Testing: CHECKPOINT — Notify user to verify bolus file format and frontmatter schema

### Git

- [X] Commit, fetch/rebase, push

## Technical Notes

- **Frontmatter parsing.** Prefer `python-frontmatter` if it's lightweight enough (check: weekly downloads, last publish, maintenance). Fallback: a simple YAML parser between `---` delimiters using `pyyaml`. The goal is minimal dependencies.
- **Unknown fields preserved.** Bolus frontmatter must preserve fields the library doesn't know about. This supports future extensions (dynamic routing rules, confidence scores, provenance metadata) without requiring schema migrations.
- **File-per-bolus.** Each bolus is one file. No multi-bolus files. This keeps git diffs clean and allows per-bolus operations without parsing a larger structure.
- **No search in Phase 1.** `list_boluses` returns metadata; `read_bolus` retrieves by ID. There is no keyword search across bolus content. If a future phase needs FTS5, it will be a new `SqliteBolusStore` implementation, not a modification to `MarkdownBolusStore`.
- **The `summary` field is critical.** It is the one-line entry that appears in the Circle 1 manifest. It must be human-curated and concise. The assembler (S04) reads this field to build the manifest section of `anamnesis.md`.

## Blockers

- F01-S01 (Project Scaffolding) — depends on `BolusStore` ABC and `KnowledgeConfig`.
