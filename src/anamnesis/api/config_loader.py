"""Config file loading for the API and CLI."""

from __future__ import annotations

import json
import os
from pathlib import Path

import yaml

from anamnesis.config import KnowledgeConfig

_DEFAULT_FILENAMES = ["anamnesis.yaml", "anamnesis.yml", "anamnesis.json"]


def load_config(config_path: str | Path | None = None) -> KnowledgeConfig:
    """Load a KnowledgeConfig from a file.

    Resolution order:
    1. Explicit config_path argument
    2. ANAMNESIS_CONFIG environment variable
    3. Default filenames in current directory
    """
    path = _resolve_path(config_path)

    if path is None:
        raise FileNotFoundError(
            "No config file found. Provide a path, set ANAMNESIS_CONFIG, "
            f"or create one of: {', '.join(_DEFAULT_FILENAMES)}"
        )

    text = path.read_text(encoding="utf-8")

    if path.suffix == ".json":
        data = json.loads(text)
    else:
        data = yaml.safe_load(text)

    # Coerce path strings
    for key in ("circle1_path", "circle2_root"):
        if key in data and isinstance(data[key], str):
            data[key] = Path(data[key])

    # Flatten nested completion_provider block
    if "completion_provider" in data:
        cp = data.pop("completion_provider") or {}
        if isinstance(cp, dict):
            data.setdefault("completion_provider_type", cp.get("type"))
            data.setdefault("completion_provider_base_url", cp.get("base_url"))
            data.setdefault("completion_provider_model", cp.get("model"))
            data.setdefault("completion_provider_api_key", cp.get("api_key"))

    # Strip fields that aren't KnowledgeConfig parameters
    import dataclasses
    valid_fields = {f.name for f in dataclasses.fields(KnowledgeConfig)}
    config_data = {k: v for k, v in data.items() if k in valid_fields}

    return KnowledgeConfig(**config_data)


def _resolve_path(config_path: str | Path | None) -> Path | None:
    if config_path is not None:
        p = Path(config_path)
        if p.exists():
            return p
        raise FileNotFoundError(f"Config file not found: {p}")

    env_path = os.environ.get("ANAMNESIS_CONFIG")
    if env_path:
        p = Path(env_path)
        if p.exists():
            return p
        raise FileNotFoundError(f"ANAMNESIS_CONFIG points to missing file: {p}")

    for name in _DEFAULT_FILENAMES:
        p = Path(name)
        if p.exists():
            return p

    return None
