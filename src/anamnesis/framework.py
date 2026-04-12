"""KnowledgeFramework — main entry point for the Anamnesis library."""

from __future__ import annotations

from anamnesis.bolus.base import BolusStore
from anamnesis.bolus.store import validate_bolus_id, slugify
from anamnesis.config import KnowledgeConfig


class KnowledgeFramework:
    """Central orchestrator for the Anamnesis knowledge management framework.

    Accepts a KnowledgeConfig, validates it, and wires up the appropriate
    storage backend.
    """

    def __init__(self, config: KnowledgeConfig) -> None:
        self.config = config
        self._store = self._init_store()

    @property
    def store(self) -> BolusStore:
        """The active bolus store backend."""
        return self._store

    def _init_store(self) -> BolusStore:
        if self.config.bolus_store == "markdown":
            from anamnesis.bolus.store import MarkdownBolusStore

            return MarkdownBolusStore(self.config.circle2_root)

        raise ValueError(f"Unknown bolus_store: {self.config.bolus_store!r}")

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
        """Create a new bolus. Raises ValueError if it already exists.

        Args:
            render: "inline" (full text in injection) or "reference" (manifest
                    line with retrieval pointer). Default: "reference".
            priority: Ordering within the injection. Lower = earlier.
                      Suggested ranges: 1-20 identity/context, 50 knowledge,
                      90+ constraints.
        """
        bolus_id = slugify(bolus_id) if not _is_slug(bolus_id) else bolus_id
        validate_bolus_id(bolus_id)

        if self._store.exists(bolus_id):
            raise ValueError(f"Bolus {bolus_id!r} already exists.")

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
        """Read bolus content by ID."""
        return self._store.read(bolus_id)

    def update_bolus(self, bolus_id: str, content: str) -> None:
        """Update an existing bolus's content, preserving metadata."""
        meta = self._store.get_metadata(bolus_id)
        self._store.write(bolus_id, content, meta)

    def delete_bolus(self, bolus_id: str) -> bool:
        """Delete a bolus. Returns True if it existed."""
        return self._store.delete(bolus_id)

    def list_boluses(self, active_only: bool = True) -> list[dict]:
        """List bolus metadata. By default only active boluses."""
        return self._store.list(active_only=active_only)

    def set_bolus_active(self, bolus_id: str, active: bool) -> None:
        """Toggle bolus activation state."""
        self._store.set_active(bolus_id, active)

    def get_bolus_metadata(self, bolus_id: str) -> dict:
        """Return frontmatter metadata for a bolus."""
        return self._store.get_metadata(bolus_id)

    def retrieve(self, bolus_id: str) -> str:
        """Retrieve bolus content by categorical pointer (alias for read_bolus)."""
        return self.read_bolus(bolus_id)

    # ─── Circle 1: Injection Assembly ─────────────────────────────

    def get_injection(self) -> str:
        """Assemble and return the injection document as a string."""
        from anamnesis.inject.assembler import assemble

        text, _ = assemble(
            self._store,
            soft_max=self.config.circle1_max_tokens,
        )
        return text

    def assemble(self) -> "Path":
        """Assemble and write the injection document to circle1_path."""
        from pathlib import Path

        text = self.get_injection()
        self.config.circle1_path.parent.mkdir(parents=True, exist_ok=True)
        self.config.circle1_path.write_text(text, encoding="utf-8")
        return self.config.circle1_path

    def get_injection_metrics(self) -> dict:
        """Return token counts, budget utilization, and bolus statistics."""
        from anamnesis.inject.assembler import assemble

        text, budget = assemble(
            self._store,
            soft_max=self.config.circle1_max_tokens,
        )

        all_boluses = self._store.list(active_only=False)
        active_boluses = [b for b in all_boluses if b.get("active", True)]

        return {
            "total_tokens": budget.token_count,
            "soft_max": budget.soft_max,
            "hard_ceiling": budget.hard_ceiling,
            "utilization_pct": budget.utilization_pct,
            "status": budget.status,
            "active_boluses": len(active_boluses),
            "total_boluses": len(all_boluses),
        }


def _is_slug(text: str) -> bool:
    """Check if text is already a valid slug."""
    import re

    return bool(re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", text))
