"""KnowledgeFramework — main entry point for the Anamnesis library."""

from __future__ import annotations

from pathlib import Path

from anamnesis.bolus.base import BolusStore
from anamnesis.bolus.store import is_valid_bolus_id, validate_bolus_id, slugify
from anamnesis.config import KnowledgeConfig
from anamnesis.exceptions import BolusExistsError, BolusNotFoundError, CircleNotConfiguredError


class KnowledgeFramework:
    """Central orchestrator for the Anamnesis knowledge management framework."""

    def __init__(self, config: KnowledgeConfig) -> None:
        self.config = config
        self._store = self._init_store()
        self._episode_store = self._init_episode_store()
        self._curation_store = self._init_curation_store()
        self._completion_provider = self._init_completion_provider()
        self._current_turns: list = []
        self._session_started: str | None = None

    @property
    def store(self) -> BolusStore:
        return self._store

    def _init_store(self) -> BolusStore:
        if self.config.bolus_store == "markdown":
            from anamnesis.bolus.store import MarkdownBolusStore

            return MarkdownBolusStore(self.config.circle2_root)

        raise ValueError(f"Unknown bolus_store: {self.config.bolus_store!r}")

    def _init_episode_store(self):
        if self.config.circle4_root is None:
            return None
        from anamnesis.episode.store import EpisodeStore

        db_path = self.config.circle4_root / "anamnesis.db"
        return EpisodeStore(db_path)

    def _init_curation_store(self):
        if self.config.circle4_root is None:
            return None
        from anamnesis.curation.store import CurationStore

        db_path = self.config.circle4_root / "anamnesis.db"
        return CurationStore(db_path)

    def _init_completion_provider(self):
        if self.config.completion_provider_type == "openai_compatible":
            from anamnesis.completion.openai_compat import OpenAICompatibleProvider

            return OpenAICompatibleProvider(
                base_url=self.config.completion_provider_base_url or "",
                model=self.config.completion_provider_model or "",
                api_key=self.config.completion_provider_api_key,
            )
        return None

    # ─── Circle 2: Bolus CRUD ──────────────────────────────────────

    def create_bolus(
        self,
        bolus_id: str,
        content: str,
        *,
        title: str | None = None,
        summary: str = "",
        render: str = "reference",
        priority: int = 50,
        tags: list[str] | None = None,
    ) -> None:
        """Create a new bolus. Raises ValueError if it already exists."""
        bolus_id = bolus_id if is_valid_bolus_id(bolus_id) else slugify(bolus_id)
        validate_bolus_id(bolus_id)

        if self._store.exists(bolus_id):
            raise BolusExistsError(bolus_id)

        metadata = {
            "id": bolus_id,
            "title": title or bolus_id.replace("-", " ").title(),
            "active": True,
            "render": render,
            "priority": priority,
            "summary": summary,
            "tags": tags or [],
        }
        self._store.write(bolus_id, content, metadata)

    def read_bolus(self, bolus_id: str) -> str:
        return self._store.read(bolus_id)

    def update_bolus(self, bolus_id: str, content: str) -> None:
        """Update an existing bolus's content, preserving metadata."""
        meta = self._store.get_metadata(bolus_id)
        self._store.write(bolus_id, content, meta)

    def delete_bolus(self, bolus_id: str) -> bool:
        """Delete a bolus. System boluses (IDs starting with _) cannot be deleted."""
        if bolus_id.startswith("_"):
            raise ValueError(f"Cannot delete system bolus '{bolus_id}'.")
        return self._store.delete(bolus_id)

    def list_boluses(
        self, active_only: bool = True, include_system: bool = False
    ) -> list[dict]:
        """List bolus metadata. By default excludes system boluses."""
        boluses = self._store.list(active_only=active_only)
        if not include_system:
            boluses = [b for b in boluses if not b.get("id", "").startswith("_")]
        return boluses

    def set_bolus_active(self, bolus_id: str, active: bool) -> None:
        self._store.set_active(bolus_id, active)

    def get_bolus_metadata(self, bolus_id: str) -> dict:
        return self._store.get_metadata(bolus_id)

    def upsert_bolus(
        self,
        bolus_id: str,
        content: str,
        *,
        title: str | None = None,
        summary: str | None = None,
        render: str = "reference",
        priority: int = 50,
        tags: list[str] | None = None,
    ) -> str:
        """Create or replace a bolus.

        If the bolus exists, its content is replaced and metadata is preserved.
        If it does not exist, a new bolus is created with the provided (or default) metadata.
        Returns "created" or "updated".
        """
        bolus_id = bolus_id if is_valid_bolus_id(bolus_id) else slugify(bolus_id)
        validate_bolus_id(bolus_id)

        if self._store.exists(bolus_id):
            self.update_bolus(bolus_id, content)
            return "updated"

        self.create_bolus(
            bolus_id,
            content,
            title=title,
            summary=summary or "",
            render=render,
            priority=priority,
            tags=tags,
        )
        return "created"

    def append_bolus(
        self, bolus_id: str, content: str, separator: str = "\n\n---\n\n"
    ) -> None:
        """Append content to an existing bolus.

        Raises KeyError if the bolus does not exist.
        """
        self._store.append(bolus_id, content, separator)

    def retrieve(self, bolus_id: str) -> str:
        """Retrieve bolus content by categorical pointer."""
        return self.read_bolus(bolus_id)

    # ─── Circle 1: Injection Assembly ─────────────────────────────

    def _resolve_agent_profile(self, agent: str | None) -> list[str] | None:
        """Resolve an agent's active_boluses list from the config file."""
        if agent is None:
            return None
        from anamnesis.init import load_project_config
        for name in ["anamnesis.yaml", "anamnesis.yml"]:
            p = Path(name)
            if p.exists():
                project = load_project_config(p)
                agents = project.get("agents", {})
                if agent in agents:
                    return agents[agent].get("active_boluses", [])
        return []

    def get_injection(self, agent: str | None = None) -> str:
        """Assemble and return the injection document.

        If agent is specified, applies the agent's activation profile
        and includes only that agent's recency bolus.
        """
        from anamnesis.inject.assembler import assemble

        profile = self._resolve_agent_profile(agent)
        text, _ = assemble(
            self._store,
            soft_max=self.config.circle1_max_tokens,
            agent=agent,
            agent_active_boluses=profile,
        )
        return text

    def assemble(self, agent: str | None = None) -> Path:
        """Assemble and write the injection document to circle1_path."""
        text = self.get_injection(agent=agent)
        self.config.circle1_path.parent.mkdir(parents=True, exist_ok=True)
        self.config.circle1_path.write_text(text, encoding="utf-8")
        return self.config.circle1_path

    def get_injection_metrics(self, agent: str | None = None) -> dict:
        """Return token counts, budget utilization, and bolus statistics."""
        from anamnesis.inject.assembler import assemble
        from anamnesis.inject.budget import SimpleTokenCounter
        from anamnesis.recency.pipeline import recency_bolus_id

        profile = self._resolve_agent_profile(agent)
        text, budget = assemble(
            self._store,
            soft_max=self.config.circle1_max_tokens,
            agent=agent,
            agent_active_boluses=profile,
        )

        recency_id = recency_bolus_id(agent)
        recency_tokens = 0
        if self._store.exists(recency_id):
            counter = SimpleTokenCounter()
            recency_tokens = counter.count(self._store.read(recency_id))

        return {
            "total_tokens": budget.token_count,
            "soft_max": budget.soft_max,
            "hard_ceiling": budget.hard_ceiling,
            "utilization_pct": budget.utilization_pct,
            "status": budget.status,
            "active_boluses": budget.active_boluses,
            "total_boluses": budget.total_boluses,
            "recency_tokens": recency_tokens,
            "recency_budget": self.config.recency_budget,
            "agent": agent,
        }

    # ─── Circle 4: Episode Capture ──────────────────────────────

    def capture_turn(self, role: str, content: str) -> None:
        """Append a conversation turn to the current in-memory session.

        No-op if Circle 4 is not configured.
        """
        if self._episode_store is None:
            return

        from datetime import datetime, timezone
        from anamnesis.episode.model import Turn

        now = datetime.now(timezone.utc).isoformat()

        if self._session_started is None:
            self._session_started = now

        self._current_turns.append(
            Turn(
                role=role,
                content=content,
                timestamp=now,
                sequence=len(self._current_turns),
            )
        )

    def end_session(
        self, summary: str | None = None, agent: str | None = None
    ) -> str | None:
        """End the current session and write it to SQLite.

        Returns the session_id, or None if no turns were captured or
        Circle 4 is not configured.
        """
        if self._episode_store is None or not self._current_turns:
            self._current_turns = []
            self._session_started = None
            return None

        from datetime import datetime, timezone
        from anamnesis.episode.model import Episode

        now = datetime.now(timezone.utc)
        session_id = now.strftime("%Y-%m-%dT%H-%M-%S-") + f"{now.microsecond:06d}Z"

        episode = Episode(
            session_id=session_id,
            agent=agent,
            started=self._session_started or now.isoformat(),
            ended=now.isoformat(),
            turns=list(self._current_turns),
            summary=summary,
            turn_count=len(self._current_turns),
        )

        self._episode_store.save(episode)

        self._current_turns = []
        self._session_started = None

        if self.config.recency_budget > 0:
            from anamnesis.recency.pipeline import update_recency

            update_recency(
                self._store,
                episode,
                self.config.recency_budget,
                agent=agent,
            )

        if self.config.circle4_retention_days is not None:
            self._episode_store.cleanup(self.config.circle4_retention_days)

        return session_id

    def list_episodes(self, agent: str | None = None) -> list[dict]:
        if self._episode_store is None:
            return []
        return self._episode_store.list(agent=agent)

    # ─── Circle 3: Curation Queue ──────────────────────────────

    def _require_curation_store(self):
        if self._curation_store is None:
            raise CircleNotConfiguredError(3, "circle4_root must be set.")
        return self._curation_store

    def stage(
        self,
        fact: str,
        *,
        source_episode: str | None = None,
        source_agent: str | None = None,
        source_url: str | None = None,
        suggested_bolus: str | None = None,
        confidence: float = 0.5,
    ) -> int:
        """Deposit a candidate fact in the Circle 3 curation queue.

        Returns the new item id. Used by the compilation pipeline (Circle 4 → Circle 3)
        and by external agents via the REST API (F04-S02).
        """
        store = self._require_curation_store()
        return store.stage(
            fact,
            source_episode=source_episode,
            source_agent=source_agent,
            source_url=source_url,
            suggested_bolus=suggested_bolus,
            confidence=confidence,
        )

    def get_curation_queue(self, limit: int = 50) -> list[dict]:
        """Return pending curation items ordered by confidence descending."""
        store = self._require_curation_store()
        items = store.list_pending(limit=limit)
        return [
            {
                "id": item.id,
                "fact": item.fact,
                "source_episode": item.source_episode,
                "source_agent": item.source_agent,
                "source_url": item.source_url,
                "suggested_bolus": item.suggested_bolus,
                "confidence": item.confidence,
                "status": item.status,
                "created": item.created,
            }
            for item in items
        ]

    def confirm(self, item_id: int, bolus_id: str) -> None:
        """Promote a curation item to a Circle 2 bolus.

        Appends the fact text to the target bolus (creates the bolus if it
        doesn't exist), then marks the queue item as confirmed.
        """
        store = self._require_curation_store()
        item = store.get(item_id)
        self.append_bolus(bolus_id, item.fact) if self._store.exists(bolus_id) else \
            self.create_bolus(bolus_id, item.fact, summary=f"Promoted from curation queue.")
        store.confirm(item_id)

    def reject(self, item_id: int) -> None:
        """Reject a curation item — marks as rejected, stays in DB for audit."""
        store = self._require_curation_store()
        store.reject(item_id)

    def defer(self, item_id: int) -> None:
        """Defer a curation item — keeps it pending but deprioritized."""
        store = self._require_curation_store()
        store.defer(item_id)

    # ─── Compilation Pipeline (Circle 4 → Circle 3) ────────────

    def compile(
        self,
        agent: str | None = None,
        provider=None,
    ) -> dict:
        """Extract facts from uncompiled episodes and deposit in Circle 3.

        A CompletionProvider is required — pass one explicitly or configure
        `completion_provider` in anamnesis.yaml. Raises RuntimeError if neither
        is available (no heuristic fallback for extraction).

        Returns a summary dict: {episodes_processed, facts_extracted, errors}.
        """
        if self._episode_store is None:
            raise CircleNotConfiguredError(4, "circle4_root must be set.")
        curation_store = self._require_curation_store()

        effective_provider = provider or self._completion_provider
        if effective_provider is None:
            raise RuntimeError(
                "Compilation requires a CompletionProvider. "
                "Pass one to compile() or configure completion_provider in anamnesis.yaml."
            )

        from anamnesis.compile.pipeline import compile_episodes

        result = compile_episodes(
            episode_store=self._episode_store,
            curation_store=curation_store,
            bolus_store=self._store,
            provider=effective_provider,
            agent=agent,
        )
        return {
            "episodes_processed": result.episodes_processed,
            "facts_extracted": result.facts_extracted,
            "errors": result.errors,
        }

    def get_episode(self, session_id: str):
        """Get a full episode with turns. Raises RuntimeError if Circle 4 not configured."""
        if self._episode_store is None:
            raise CircleNotConfiguredError(4)
        return self._episode_store.load(session_id)
