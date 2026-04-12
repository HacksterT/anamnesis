"""Lightweight frontmatter parsing for bolus markdown files."""

from __future__ import annotations

import yaml

_DELIMITER = "---"


def parse(text: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from a markdown string.

    Returns (metadata_dict, body_string). If no frontmatter is found,
    returns ({}, original_text).
    """
    stripped = text.lstrip("\n")
    if not stripped.startswith(_DELIMITER):
        return {}, text

    # Find the closing delimiter
    end = stripped.find(_DELIMITER, len(_DELIMITER))
    if end == -1:
        return {}, text

    yaml_block = stripped[len(_DELIMITER) : end].strip()
    body = stripped[end + len(_DELIMITER) :].lstrip("\n")

    metadata = yaml.safe_load(yaml_block)
    if not isinstance(metadata, dict):
        return {}, text

    return metadata, body


def dump(metadata: dict, body: str) -> str:
    """Serialize metadata and body into a frontmatter markdown string."""
    yaml_str = yaml.dump(
        metadata,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
    ).rstrip("\n")

    return f"---\n{yaml_str}\n---\n\n{body}"
