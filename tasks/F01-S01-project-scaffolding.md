---
id: F01-S01
feature: F01
title: Project Scaffolding & Configuration
priority: Must-Have
status: done
created: 2026-04-12
type: software
---

# F01-S01: Project Scaffolding & Configuration

**Feature:** F01 — Circle 1 & Circle 2 Core
**Priority:** Must-Have

## Summary

Set up the Python package structure, core configuration, and abstract interfaces that all subsequent stories depend on. This story produces a pip-installable library (`anamnesis`) with a `KnowledgeConfig` dataclass for per-application configuration and a `BolusStore` abstract interface for pluggable storage backends. No business logic yet — this is the foundation that S02-S05 build on.

## Acceptance Criteria

- [x] `uv sync` succeeds from the repo root and makes `anamnesis` importable
- [x] `from anamnesis import KnowledgeConfig` works and returns a dataclass with all Phase 1 fields
- [x] `from anamnesis import KnowledgeFramework` works and accepts a `KnowledgeConfig` instance
- [x] `BolusStore` is an abstract base class with methods: `read`, `write`, `delete`, `list`, `exists`
- [x] `KnowledgeConfig` includes paths for Circle 1 and Circle 2, token budget, and bolus store type
- [x] Configuration can be instantiated with only required fields (paths); all others have sensible defaults
- [x] Package has zero external runtime dependencies at this stage (FastAPI added in S05, model-specific tokenizers are optional)
- [x] uv is the package manager; `uv sync` installs the base package, `uv sync --extra api` adds FastAPI, `uv sync --extra dev` adds test/lint tools

## Tasks

### Backend

- [x] Create `pyproject.toml` with package metadata, Python 3.11+ requirement, and `[project.optional-dependencies]` groups for `api` (FastAPI) and `dev` (pytest, ruff)
- [x] Create package structure:
  ```
  src/
  └── anamnesis/
      ├── __init__.py        # Public exports: KnowledgeFramework, KnowledgeConfig
      ├── config.py           # KnowledgeConfig dataclass
      ├── framework.py        # KnowledgeFramework class (shell — methods added in S02-S04)
      ├── bolus/
      │   ├── __init__.py
      │   ├── base.py         # BolusStore ABC
      │   └── store.py        # MarkdownBolusStore (shell — implemented in S02)
      ├── inject/
      │   ├── __init__.py
      │   ├── assembler.py    # Shell — implemented in S04
      │   └── budget.py       # Shell — implemented in S04
      └── api/
          ├── __init__.py
          └── server.py        # Shell — implemented in S05
  ```
- [x] Implement `KnowledgeConfig` dataclass:
  ```python
  @dataclass
  class KnowledgeConfig:
      # Required
      circle1_path: Path          # Path to anamnesis.md (the injection file)
      circle2_root: Path          # Root directory for bolus markdown files

      # Token budget
      circle1_max_tokens: int = 4000

      # Storage backend
      bolus_store: str = "markdown"  # "markdown" (Phase 1 only)

      # API
      api_host: str = "127.0.0.1"
      api_port: int = 8741
      api_key: str | None = None     # Optional API key; None = no auth
  ```
- [x] Implement `BolusStore` abstract base class in `bolus/base.py`:
  ```python
  class BolusStore(ABC):
      @abstractmethod
      def read(self, bolus_id: str) -> str: ...
      @abstractmethod
      def write(self, bolus_id: str, content: str, metadata: dict) -> None: ...
      @abstractmethod
      def delete(self, bolus_id: str) -> bool: ...
      @abstractmethod
      def list(self, active_only: bool = True) -> list[dict]: ...
      @abstractmethod
      def exists(self, bolus_id: str) -> bool: ...
      @abstractmethod
      def get_metadata(self, bolus_id: str) -> dict: ...
      @abstractmethod
      def set_active(self, bolus_id: str, active: bool) -> None: ...
  ```
- [x] Implement `KnowledgeFramework` shell class that accepts config, validates paths, and instantiates the appropriate `BolusStore` based on `config.bolus_store`

### Testing & Verification

- [x] Write tests: KnowledgeConfig instantiation with defaults, required field validation, BolusStore ABC cannot be instantiated directly
- [x] Local Testing: `pytest tests/` passes, `uv sync` succeeds, imports work
- [x] Manual Testing: CHECKPOINT — Notify user to verify package structure and interface design

### Git

- [ ] Commit, fetch/rebase, push

## Technical Notes

- The package is named `anamnesis` (not `knowledge-framework` as in the construction doc). The construction doc's package name was a placeholder.
- **uv is the package manager.** All commands use `uv sync`, `uv run pytest`, `uv run anamnesis serve`. No pip, no virtualenv management. uv handles it.
- `KnowledgeFramework` is the main entry point. Methods are added as shells in this story and implemented in S02-S04. This avoids circular imports and lets each story add its own functionality.
- No `CompletionProvider` interface in Phase 1. It will be added when Phase 3 (compilation pipeline) is built.
- The `bolus_store` config field is a string discriminator, not a class reference. This keeps the config serializable (JSON/YAML friendly for the API layer).
- **No Docker in Phase 1.** Development and testing run locally with uv. A convenience Dockerfile is added in S05 for deployment but is not required for any workflow.

## Blockers

None — this is the first story.
