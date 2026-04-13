"""Tests for per-agent injection routing and recency isolation."""

from pathlib import Path

import pytest
import yaml

from anamnesis import KnowledgeConfig, KnowledgeFramework
from anamnesis.init import init_project, register_agent
from anamnesis.recency.pipeline import recency_bolus_id


@pytest.fixture
def multi_agent_env(tmp_path: Path, monkeypatch):
    """Set up a multi-agent environment with two agents and shared boluses."""
    monkeypatch.chdir(tmp_path)
    config_path = init_project(Path("knowledge"))

    # Register two agents with different activation profiles
    register_agent(config_path, "cto", active_boluses=["infra", "skill-deep-research"])
    register_agent(config_path, "cpo", active_boluses=["theology", "skill-scripture"], recency_budget=400)

    cfg = KnowledgeConfig(
        circle1_path=tmp_path / "knowledge" / "anamnesis.md",
        circle2_root=tmp_path / "knowledge" / "boluses",
        circle4_root=tmp_path / "knowledge" / "episodes",
        recency_budget=400,
    )
    kf = KnowledgeFramework(cfg)

    # Create shared boluses (active by default — both agents see these)
    kf.create_bolus("identity", "Physician-builder.", render="inline", priority=10, summary="Identity.")
    kf.create_bolus("constraints", "Do not hallucinate.", render="inline", priority=90, summary="Rules.")

    # Create agent-specific boluses (inactive by default — only activated agents see these)
    kf.create_bolus("infra", "Mac Mini M4 Pro.", summary="Infrastructure.")
    kf.set_bolus_active("infra", False)  # Only CTO gets this via profile

    kf.create_bolus("theology", "Systematic theology notes.", summary="Theology.")
    kf.set_bolus_active("theology", False)  # Only CPO gets this via profile

    kf.create_bolus("skill-deep-research", "Multi-source research skill.", summary="Research.", tags=["skill"])
    kf.set_bolus_active("skill-deep-research", False)

    kf.create_bolus("skill-scripture", "Bible search skill.", summary="Scripture.", tags=["skill"])
    kf.set_bolus_active("skill-scripture", False)

    # Create a bolus both agents see (active by default)
    kf.create_bolus("projects", "Anamnesis, Ezra, Cortivus.", summary="Active projects.")

    return kf


class TestAgentProfiles:
    def test_agent_config_has_active_boluses(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        config_path = init_project(Path("knowledge"))
        register_agent(config_path, "cto", active_boluses=["infra", "skills"])
        data = yaml.safe_load(config_path.read_text())
        assert data["agents"]["cto"]["active_boluses"] == ["infra", "skills"]

    def test_empty_active_boluses_default(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        config_path = init_project(Path("knowledge"))
        register_agent(config_path, "cto")
        data = yaml.safe_load(config_path.read_text())
        assert data["agents"]["cto"]["active_boluses"] == []


class TestInjectionRouting:
    def test_cto_gets_infra_not_theology(self, multi_agent_env) -> None:
        kf = multi_agent_env
        injection = kf.get_injection(agent="cto")
        assert "infra" in injection  # CTO's activated bolus
        assert "theology" not in injection  # CPO's bolus, not CTO's

    def test_cpo_gets_theology_not_infra(self, multi_agent_env) -> None:
        kf = multi_agent_env
        injection = kf.get_injection(agent="cpo")
        assert "theology" in injection
        assert "infra" not in injection

    def test_both_agents_see_default_active_boluses(self, multi_agent_env) -> None:
        kf = multi_agent_env
        cto_injection = kf.get_injection(agent="cto")
        cpo_injection = kf.get_injection(agent="cpo")
        # Both see identity (inline, active by default)
        assert "Physician-builder." in cto_injection
        assert "Physician-builder." in cpo_injection
        # Both see projects (reference, active by default)
        assert "projects" in cto_injection
        assert "projects" in cpo_injection

    def test_default_injection_no_agent(self, multi_agent_env) -> None:
        kf = multi_agent_env
        injection = kf.get_injection()  # No agent
        # Should include default-active boluses only
        assert "Physician-builder." in injection
        assert "projects" in injection
        # Should NOT include agent-specific boluses (they're inactive by default)
        assert "infra" not in injection
        assert "theology" not in injection

    def test_cto_sees_skill_boluses(self, multi_agent_env) -> None:
        kf = multi_agent_env
        injection = kf.get_injection(agent="cto")
        assert "skill-deep-research" in injection
        assert "skill-scripture" not in injection


class TestRecencyIsolation:
    def test_per_agent_recency_bolus_ids(self) -> None:
        assert recency_bolus_id("cto") == "_recency-cto"
        assert recency_bolus_id("cpo") == "_recency-cpo"
        assert recency_bolus_id(None) == "_recency"

    def test_agents_get_separate_recency(self, multi_agent_env) -> None:
        kf = multi_agent_env

        # CTO session
        kf.capture_turn("user", "Let's review the infrastructure")
        kf.end_session(agent="cto")

        # CPO session
        kf.capture_turn("user", "Let's study Romans 8")
        kf.end_session(agent="cpo")

        # Both recency boluses should exist
        assert kf.store.exists("_recency-cto")
        assert kf.store.exists("_recency-cpo")

        # CTO injection should have CTO recency, not CPO's
        cto_injection = kf.get_injection(agent="cto")
        assert "infrastructure" in cto_injection
        assert "Romans" not in cto_injection

        # CPO injection should have CPO recency, not CTO's
        cpo_injection = kf.get_injection(agent="cpo")
        assert "Romans" in cpo_injection
        assert "infrastructure" not in cpo_injection

    def test_default_injection_excludes_agent_recency(self, multi_agent_env) -> None:
        kf = multi_agent_env
        kf.capture_turn("user", "Agent-specific context")
        kf.end_session(agent="cto")

        # Default injection should NOT include agent-specific recency
        injection = kf.get_injection()
        assert "_recency-cto" not in injection

    def test_metrics_per_agent(self, multi_agent_env) -> None:
        kf = multi_agent_env
        kf.capture_turn("user", "Test session")
        kf.end_session(agent="cto")

        metrics = kf.get_injection_metrics(agent="cto")
        assert metrics["agent"] == "cto"
        assert metrics["recency_tokens"] > 0
