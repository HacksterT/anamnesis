"""Tests for CLI commands."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
import yaml

from anamnesis.cli import main
from anamnesis.init import init_project, register_agent, load_project_config


# ─── Init ────────────────────────────────────────────────────────


class TestInit:
    def test_init_creates_structure(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        config_path = init_project(Path("knowledge"))

        assert (tmp_path / "knowledge" / "anamnesis.md").exists()
        assert (tmp_path / "knowledge" / "boluses").is_dir()
        assert config_path.exists()

        data = yaml.safe_load(config_path.read_text())
        assert data["circle1_path"] == "knowledge/anamnesis.md"
        assert data["circle2_root"] == "knowledge/boluses"

    def test_init_does_not_overwrite_existing_config(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        init_project(Path("knowledge"))
        # Add custom field
        config_path = Path("anamnesis.yaml")
        data = yaml.safe_load(config_path.read_text())
        data["custom_field"] = "keep me"
        config_path.write_text(yaml.dump(data))

        # Re-init
        init_project(Path("knowledge"))
        data = yaml.safe_load(config_path.read_text())
        assert data["custom_field"] == "keep me"

    def test_register_agent(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        config_path = init_project(Path("knowledge"))
        register_agent(config_path, "atlas", token_budget=4000, recency_budget=500)

        data = yaml.safe_load(config_path.read_text())
        assert "atlas" in data["agents"]
        assert data["agents"]["atlas"]["token_budget"] == 4000
        assert data["agents"]["atlas"]["recency_budget"] == 500

    def test_register_duplicate_agent_raises(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        config_path = init_project(Path("knowledge"))
        register_agent(config_path, "atlas")
        with pytest.raises(ValueError, match="already registered"):
            register_agent(config_path, "atlas")


# ─── CLI init command ─────────────────────────────────────────────


class TestCLIInit:
    def test_cli_init(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        main(["init"])
        assert (tmp_path / "knowledge" / "anamnesis.md").exists()
        assert (tmp_path / "anamnesis.yaml").exists()

    def test_cli_init_with_agent(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        main(["init", "--agent", "selah", "--recency-budget", "200"])
        data = yaml.safe_load((tmp_path / "anamnesis.yaml").read_text())
        assert "selah" in data["agents"]
        assert data["agents"]["selah"]["recency_budget"] == 200


# ─── CLI bolus commands ───────────────────────────────────────────


@pytest.fixture
def cli_env(tmp_path: Path, monkeypatch):
    """Set up a working CLI environment with config and a bolus."""
    monkeypatch.chdir(tmp_path)
    init_project(Path("knowledge"))

    # Create a bolus via the library (not CLI) for test fixtures
    from anamnesis.api.config_loader import load_config
    from anamnesis.framework import KnowledgeFramework
    config = load_config(str(tmp_path / "anamnesis.yaml"))
    kf = KnowledgeFramework(config)
    kf.create_bolus("infra", "Mac Mini M4 Pro.", summary="Server details.", tags=["tech"])
    kf.create_bolus("identity", "Physician-builder.", render="inline", priority=10, summary="Identity.")
    return tmp_path


class TestCLIBolus:
    def test_bolus_list(self, cli_env, capsys) -> None:
        main(["bolus", "list"])
        out = capsys.readouterr().out
        assert "infra" in out
        assert "identity" in out

    def test_bolus_list_json(self, cli_env, capsys) -> None:
        main(["bolus", "list", "--json"])
        out = capsys.readouterr().out
        data = json.loads(out)
        assert len(data) == 2
        ids = {b["id"] for b in data}
        assert "infra" in ids

    def test_bolus_show(self, cli_env, capsys) -> None:
        main(["bolus", "show", "infra"])
        out = capsys.readouterr().out
        assert "Mac Mini" in out
        assert "Server details." in out

    def test_bolus_show_json(self, cli_env, capsys) -> None:
        main(["bolus", "show", "infra", "--json"])
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["id"] == "infra"
        assert "Mac Mini" in data["content"]

    def test_bolus_show_not_found(self, cli_env) -> None:
        with pytest.raises(SystemExit) as exc:
            main(["bolus", "show", "nonexistent"])
        assert exc.value.code == 1

    def test_bolus_create_from_file(self, cli_env, capsys) -> None:
        content_file = cli_env / "test_content.md"
        content_file.write_text("New bolus content here.")
        main(["bolus", "create", "new-bolus", "--summary", "A test.", "--file", str(content_file)])
        out = capsys.readouterr().out
        assert "Created: new-bolus" in out

        # Verify it exists
        main(["bolus", "show", "new-bolus"])
        out = capsys.readouterr().out
        assert "New bolus content here." in out

    def test_bolus_activate_deactivate(self, cli_env, capsys) -> None:
        main(["bolus", "deactivate", "infra"])
        out = capsys.readouterr().out
        assert "Deactivated: infra" in out

        main(["bolus", "list", "--json"])
        out = capsys.readouterr().out
        data = json.loads(out)
        ids = {b["id"] for b in data}
        assert "infra" not in ids  # active_only by default

        main(["bolus", "activate", "infra"])
        out = capsys.readouterr().out
        assert "Activated: infra" in out

    def test_bolus_delete(self, cli_env, capsys) -> None:
        main(["bolus", "delete", "infra"])
        out = capsys.readouterr().out
        assert "Deleted: infra" in out

    def test_bolus_delete_not_found(self, cli_env) -> None:
        with pytest.raises(SystemExit) as exc:
            main(["bolus", "delete", "nonexistent"])
        assert exc.value.code == 1


# ─── CLI agent commands ───────────────────────────────────────────


class TestCLIAgent:
    def test_agent_list_empty(self, cli_env, capsys) -> None:
        main(["agent", "list"])
        out = capsys.readouterr().out
        assert "No agents" in out

    def test_agent_register_and_list(self, cli_env, capsys) -> None:
        main(["init", "--agent", "atlas"])
        main(["agent", "list"])
        out = capsys.readouterr().out
        assert "atlas" in out

    def test_agent_show(self, cli_env, capsys) -> None:
        main(["init", "--agent", "atlas"])
        main(["agent", "show", "atlas"])
        out = capsys.readouterr().out
        assert "atlas" in out
        assert "4000" in out  # token budget

    def test_agent_show_json(self, cli_env, capsys) -> None:
        main(["init", "--agent", "atlas"])
        capsys.readouterr()  # clear init output
        main(["agent", "show", "atlas", "--json"])
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["name"] == "atlas"
        assert data["token_budget"] == 4000

    def test_agent_show_not_found(self, cli_env) -> None:
        with pytest.raises(SystemExit) as exc:
            main(["agent", "show", "nonexistent"])
        assert exc.value.code == 1

    def test_agent_recency(self, cli_env, capsys) -> None:
        main(["init", "--agent", "atlas"])
        main(["agent", "recency", "atlas", "--budget", "600"])
        out = capsys.readouterr().out
        assert "600" in out

        # Verify it persisted
        main(["agent", "show", "atlas", "--json"])
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["recency_budget"] == 600

    def test_agent_list_json(self, cli_env, capsys) -> None:
        main(["init", "--agent", "atlas"])
        main(["init", "--agent", "selah", "--recency-budget", "200"])
        capsys.readouterr()  # clear init output
        main(["agent", "list", "--json"])
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "atlas" in data
        assert "selah" in data


# ─── CLI metrics/assemble/validate ────────────────────────────────


class TestCLIExistingCommands:
    def test_metrics(self, cli_env, capsys) -> None:
        main(["metrics"])
        out = capsys.readouterr().out
        assert "Tokens:" in out
        assert "active" in out

    def test_metrics_json(self, cli_env, capsys) -> None:
        main(["metrics", "--json"])
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "total_tokens" in data

    def test_assemble(self, cli_env, capsys) -> None:
        main(["assemble"])
        out = capsys.readouterr().out
        assert "Assembled:" in out
        assert (cli_env / "knowledge" / "anamnesis.md").exists()

    def test_validate(self, cli_env, capsys) -> None:
        # Assemble first so there's content
        main(["assemble"])
        main(["validate"])
        out = capsys.readouterr().out
        assert "OK" in out
