"""Project initialization and agent registry management."""

from __future__ import annotations

from pathlib import Path

import yaml


def init_project(
    knowledge_dir: Path,
    token_budget: int = 4000,
) -> Path:
    """Initialize a knowledge directory and config file.

    Creates:
    - {knowledge_dir}/anamnesis.md (empty Circle 1 placeholder)
    - {knowledge_dir}/boluses/ (Circle 2 directory)
    - anamnesis.yaml (config file in current directory)

    Returns the path to the config file.
    """
    # Create directory structure
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    boluses_dir = knowledge_dir / "boluses"
    boluses_dir.mkdir(exist_ok=True)

    # Create placeholder anamnesis.md
    injection_path = knowledge_dir / "anamnesis.md"
    if not injection_path.exists():
        injection_path.write_text(
            "<knowledge>\n\n</knowledge>\n",
            encoding="utf-8",
        )

    # Create config file
    config_path = Path("anamnesis.yaml")
    if config_path.exists():
        # Don't overwrite — update if needed
        project = load_project_config(config_path)
    else:
        project = {}

    project.setdefault("circle1_path", str(injection_path))
    project.setdefault("circle2_root", str(boluses_dir))
    project.setdefault("circle1_max_tokens", token_budget)
    project.setdefault("agents", {})

    save_project_config(config_path, project)
    return config_path


def register_agent(
    config_path: Path,
    name: str,
    token_budget: int = 4000,
    recency_budget: int = 400,
    knowledge_dir: str | None = None,
    active_boluses: list[str] | None = None,
) -> None:
    """Register an agent in the config file.

    Args:
        active_boluses: List of bolus IDs to activate for this agent
            beyond the defaults. Empty list or None means use defaults only.

    Raises ValueError if the agent already exists.
    """
    project = load_project_config(config_path)
    agents = project.setdefault("agents", {})

    if name in agents:
        raise ValueError(f"Agent '{name}' already registered.")

    agents[name] = {
        "token_budget": token_budget,
        "recency_budget": recency_budget,
        "active_boluses": active_boluses or [],
    }
    if knowledge_dir:
        agents[name]["knowledge_dir"] = knowledge_dir

    save_project_config(config_path, project)


def load_project_config(config_path: Path) -> dict:
    """Load the anamnesis.yaml project config as a dict."""
    if not config_path.exists():
        return {}
    text = config_path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    return data if isinstance(data, dict) else {}


def save_project_config(config_path: Path, data: dict) -> None:
    """Write the project config to anamnesis.yaml."""
    config_path.write_text(
        yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
