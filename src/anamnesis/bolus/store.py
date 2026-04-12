"""Markdown-based bolus store — Circle 2 storage backend."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from anamnesis.bolus.base import BolusStore
from anamnesis.bolus import frontmatter

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

_REQUIRED_METADATA = {"id", "title", "active", "summary", "created", "updated"}


def validate_bolus_id(bolus_id: str) -> str:
    """Validate and return a bolus ID, or raise ValueError."""
    if not _SLUG_RE.match(bolus_id):
        raise ValueError(
            f"Invalid bolus ID {bolus_id!r}. "
            "Must be lowercase alphanumeric with hyphens (e.g. 'my-bolus')."
        )
    return bolus_id


def slugify(text: str) -> str:
    """Convert text to a valid bolus ID slug."""
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    if not s:
        raise ValueError(f"Cannot slugify {text!r} to a valid bolus ID.")
    return s


class MarkdownBolusStore(BolusStore):
    """Stores boluses as markdown files with YAML frontmatter.

    Each bolus is a single .md file under the configured root directory.
    """

    def __init__(self, root: Path) -> None:
        self.root = root

    def _path(self, bolus_id: str) -> Path:
        return self.root / f"{bolus_id}.md"

    def read(self, bolus_id: str) -> str:
        validate_bolus_id(bolus_id)
        path = self._path(bolus_id)
        if not path.exists():
            raise KeyError(f"Bolus {bolus_id!r} not found.")
        _, body = frontmatter.parse(path.read_text(encoding="utf-8"))
        return body

    def write(self, bolus_id: str, content: str, metadata: dict) -> None:
        validate_bolus_id(bolus_id)
        self.root.mkdir(parents=True, exist_ok=True)

        today = date.today().isoformat()

        # Build full metadata, preserving extra fields from caller
        full = dict(metadata)
        full.setdefault("id", bolus_id)
        full.setdefault("active", True)
        full.setdefault("created", today)
        full["updated"] = today

        # Validate required fields present
        missing = _REQUIRED_METADATA - set(full.keys())
        if missing:
            raise ValueError(
                f"Bolus metadata missing required fields: {missing}"
            )

        path = self._path(bolus_id)
        path.write_text(frontmatter.dump(full, content), encoding="utf-8")

    def delete(self, bolus_id: str) -> bool:
        validate_bolus_id(bolus_id)
        path = self._path(bolus_id)
        if not path.exists():
            return False
        path.unlink()
        return True

    def list(self, active_only: bool = True) -> list[dict]:
        if not self.root.exists():
            return []
        results = []
        for path in sorted(self.root.glob("*.md")):
            meta, _ = frontmatter.parse(path.read_text(encoding="utf-8"))
            if not meta:
                continue
            if active_only and not meta.get("active", True):
                continue
            results.append(meta)
        return results

    def exists(self, bolus_id: str) -> bool:
        validate_bolus_id(bolus_id)
        return self._path(bolus_id).exists()

    def get_metadata(self, bolus_id: str) -> dict:
        validate_bolus_id(bolus_id)
        path = self._path(bolus_id)
        if not path.exists():
            raise KeyError(f"Bolus {bolus_id!r} not found.")
        meta, _ = frontmatter.parse(path.read_text(encoding="utf-8"))
        return meta

    def set_active(self, bolus_id: str, active: bool) -> None:
        validate_bolus_id(bolus_id)
        path = self._path(bolus_id)
        if not path.exists():
            raise KeyError(f"Bolus {bolus_id!r} not found.")

        text = path.read_text(encoding="utf-8")
        meta, body = frontmatter.parse(text)
        meta["active"] = active
        meta["updated"] = date.today().isoformat()
        path.write_text(frontmatter.dump(meta, body), encoding="utf-8")
