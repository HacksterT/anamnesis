"""Markdown-based bolus store — Circle 2 storage backend."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from anamnesis.bolus.base import BolusStore
from anamnesis.bolus import frontmatter
from anamnesis.inject.schema import VALID_RENDER_MODES

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SYSTEM_ID_RE = re.compile(r"^_[a-z0-9]+(?:-[a-z0-9]+)*$")

_REQUIRED_METADATA = {"id", "title", "active", "render", "summary", "created", "updated"}


def is_valid_bolus_id(bolus_id: str) -> bool:
    """Check if a string is a valid bolus ID (slug or system ID)."""
    return bool(_SLUG_RE.match(bolus_id) or _SYSTEM_ID_RE.match(bolus_id))


def validate_bolus_id(bolus_id: str) -> str:
    """Validate and return a bolus ID, or raise ValueError."""
    if is_valid_bolus_id(bolus_id):
        return bolus_id
    raise ValueError(
        f"Invalid bolus ID {bolus_id!r}. "
        "Must be lowercase alphanumeric with hyphens (e.g. 'my-bolus')."
    )


def slugify(text: str) -> str:
    """Convert text to a valid bolus ID slug."""
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    if not s:
        raise ValueError(f"Cannot slugify {text!r} to a valid bolus ID.")
    return s


class MarkdownBolusStore(BolusStore):
    """Stores boluses as markdown files with YAML frontmatter."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def _path(self, bolus_id: str) -> Path:
        return self.root / f"{bolus_id}.md"

    def read(self, bolus_id: str) -> str:
        validate_bolus_id(bolus_id)
        try:
            text = self._path(bolus_id).read_text(encoding="utf-8")
        except FileNotFoundError:
            raise KeyError(f"Bolus {bolus_id!r} not found.")
        _, body = frontmatter.parse(text)
        return body

    def write(self, bolus_id: str, content: str, metadata: dict) -> None:
        validate_bolus_id(bolus_id)
        self.root.mkdir(parents=True, exist_ok=True)

        today = date.today().isoformat()

        full = dict(metadata)
        full.setdefault("id", bolus_id)
        full.setdefault("active", True)
        full.setdefault("render", "reference")
        full.setdefault("priority", 50)
        full.setdefault("created", today)
        full["updated"] = today

        missing = _REQUIRED_METADATA - set(full.keys())
        if missing:
            raise ValueError(
                f"Bolus metadata missing required fields: {missing}"
            )

        if full["render"] not in VALID_RENDER_MODES:
            raise ValueError(
                f"render must be one of {VALID_RENDER_MODES}, "
                f"got {full['render']!r}"
            )

        self._path(bolus_id).write_text(
            frontmatter.dump(full, content), encoding="utf-8"
        )

    def delete(self, bolus_id: str) -> bool:
        validate_bolus_id(bolus_id)
        try:
            self._path(bolus_id).unlink()
            return True
        except FileNotFoundError:
            return False

    def list(self, active_only: bool = True) -> list[dict]:
        if not self.root.exists():
            return []
        results = []
        for path in sorted(self.root.glob("*.md")):
            meta = frontmatter.parse_metadata(path.read_text(encoding="utf-8"))
            if not meta:
                continue
            if active_only and not meta.get("active", True):
                continue
            results.append(meta)
        return results

    def read_full(self, bolus_id: str) -> tuple[dict, str]:
        """Read both metadata and content in a single parse. Returns (metadata, body)."""
        validate_bolus_id(bolus_id)
        try:
            text = self._path(bolus_id).read_text(encoding="utf-8")
        except FileNotFoundError:
            raise KeyError(f"Bolus {bolus_id!r} not found.")
        return frontmatter.parse(text)

    def exists(self, bolus_id: str) -> bool:
        validate_bolus_id(bolus_id)
        return self._path(bolus_id).exists()

    def get_metadata(self, bolus_id: str) -> dict:
        validate_bolus_id(bolus_id)
        try:
            text = self._path(bolus_id).read_text(encoding="utf-8")
        except FileNotFoundError:
            raise KeyError(f"Bolus {bolus_id!r} not found.")
        return frontmatter.parse_metadata(text)

    def set_active(self, bolus_id: str, active: bool) -> None:
        validate_bolus_id(bolus_id)
        try:
            text = self._path(bolus_id).read_text(encoding="utf-8")
        except FileNotFoundError:
            raise KeyError(f"Bolus {bolus_id!r} not found.")
        meta, body = frontmatter.parse(text)
        meta["active"] = active
        meta["updated"] = date.today().isoformat()
        self._path(bolus_id).write_text(
            frontmatter.dump(meta, body), encoding="utf-8"
        )

    def append(self, bolus_id: str, content: str, separator: str = "\n\n---\n\n") -> None:
        """Append content to an existing bolus, preserving existing content and metadata."""
        validate_bolus_id(bolus_id)
        try:
            text = self._path(bolus_id).read_text(encoding="utf-8")
        except FileNotFoundError:
            raise KeyError(f"Bolus {bolus_id!r} not found.")
        meta, body = frontmatter.parse(text)
        meta["updated"] = date.today().isoformat()
        new_body = body + separator + content if body.strip() else content
        self._path(bolus_id).write_text(
            frontmatter.dump(meta, new_body), encoding="utf-8"
        )
