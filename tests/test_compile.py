"""Tests for F03-S04: Compilation Pipeline (Circle 4 → Circle 3)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from anamnesis import KnowledgeConfig, KnowledgeFramework
from anamnesis.api.server import create_app
from anamnesis.completion.provider import StaticCompletionProvider
from anamnesis.compile.extractor import _parse_response, ExtractedFact


# ─── Fixtures ────────────────────────────────────────────────────


@pytest.fixture
def config(tmp_path: Path) -> KnowledgeConfig:
    return KnowledgeConfig(
        circle1_path=tmp_path / "anamnesis.md",
        circle2_root=tmp_path / "boluses",
        circle4_root=tmp_path,
    )


@pytest.fixture
def kf(config: KnowledgeConfig) -> KnowledgeFramework:
    return KnowledgeFramework(config)


def _json_provider(*facts: dict) -> StaticCompletionProvider:
    """Provider that returns a JSON array of facts."""
    return StaticCompletionProvider(default=json.dumps(list(facts)))


def _seed_episode(kf: KnowledgeFramework, agent: str | None = None) -> str:
    kf.capture_turn("user", "Should we use FastAPI or Flask?")
    kf.capture_turn("assistant", "FastAPI — better async support and auto-docs.")
    return kf.end_session(summary="Chose FastAPI over Flask.", agent=agent)


# ─── JSON parser (unit tests) ─────────────────────────────────────


class TestParseResponse:
    def test_clean_json_array(self) -> None:
        raw = '[{"fact": "Use FastAPI.", "suggested_bolus": "cto", "confidence": 0.9}]'
        facts = _parse_response(raw)
        assert len(facts) == 1
        assert facts[0].fact == "Use FastAPI."
        assert facts[0].confidence == 0.9

    def test_strips_markdown_fences(self) -> None:
        raw = "```json\n[{\"fact\": \"Use uv.\", \"suggested_bolus\": null, \"confidence\": 0.8}]\n```"
        facts = _parse_response(raw)
        assert len(facts) == 1
        assert facts[0].fact == "Use uv."

    def test_json_embedded_in_prose(self) -> None:
        raw = 'Here are the facts:\n[{"fact": "Use pytest.", "confidence": 0.7}]\nDone.'
        facts = _parse_response(raw)
        assert len(facts) == 1

    def test_empty_array(self) -> None:
        assert _parse_response("[]") == []

    def test_unparseable_returns_empty(self) -> None:
        assert _parse_response("No facts found in this session.") == []

    def test_missing_fact_field_skipped(self) -> None:
        raw = '[{"suggested_bolus": "cto", "confidence": 0.8}]'
        assert _parse_response(raw) == []

    def test_multiple_facts(self) -> None:
        raw = json.dumps([
            {"fact": "Fact A.", "suggested_bolus": "cto", "confidence": 0.9},
            {"fact": "Fact B.", "suggested_bolus": "infra", "confidence": 0.7},
        ])
        facts = _parse_response(raw)
        assert len(facts) == 2
        assert facts[0].fact == "Fact A."
        assert facts[1].suggested_bolus == "infra"


# ─── compile() (library) ─────────────────────────────────────────


class TestCompile:
    def test_compile_extracts_and_stages(self, kf: KnowledgeFramework) -> None:
        _seed_episode(kf)
        provider = _json_provider(
            {"fact": "Prefer FastAPI over Flask.", "suggested_bolus": "cto-knowledge", "confidence": 0.9}
        )
        result = kf.compile(provider=provider)
        assert result["episodes_processed"] == 1
        assert result["facts_extracted"] == 1
        assert result["errors"] == []

        queue = kf.get_curation_queue()
        assert len(queue) == 1
        assert queue[0]["fact"] == "Prefer FastAPI over Flask."
        assert queue[0]["source_agent"] is None

    def test_compiled_episodes_not_reprocessed(self, kf: KnowledgeFramework) -> None:
        _seed_episode(kf)
        provider = _json_provider(
            {"fact": "Fact A.", "suggested_bolus": "cto", "confidence": 0.8}
        )
        kf.compile(provider=provider)
        result2 = kf.compile(provider=provider)
        assert result2["episodes_processed"] == 0
        assert result2["facts_extracted"] == 0

    def test_compile_agent_filter(self, kf: KnowledgeFramework) -> None:
        _seed_episode(kf, agent="ezra")
        _seed_episode(kf, agent="selah")
        provider = _json_provider(
            {"fact": "Ezra fact.", "suggested_bolus": "cto", "confidence": 0.8}
        )
        result = kf.compile(agent="ezra", provider=provider)
        assert result["episodes_processed"] == 1
        # Selah's episode is still uncompiled
        selah_uncompiled = kf._episode_store.list_uncompiled(agent="selah")
        assert len(selah_uncompiled) == 1

    def test_compile_no_turns_marks_compiled(self, kf: KnowledgeFramework) -> None:
        # end_session with no captured turns returns None — so manually create
        # an episode with no turns by patching the store
        from anamnesis.episode.model import Episode
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        empty_ep = Episode(
            session_id="empty-test",
            started=now,
            ended=now,
            turns=[],
            turn_count=0,
        )
        kf._episode_store.save(empty_ep)
        provider = StaticCompletionProvider(default="[]")
        result = kf.compile(provider=provider)
        # Empty episode was processed (skipped gracefully), not counted
        assert result["episodes_processed"] == 0
        assert kf._episode_store.list_uncompiled() == []

    def test_compile_requires_circle4(self, tmp_path: Path) -> None:
        config = KnowledgeConfig(
            circle1_path=tmp_path / "anamnesis.md",
            circle2_root=tmp_path / "boluses",
        )
        kf = KnowledgeFramework(config)
        with pytest.raises(RuntimeError, match="Circle 4"):
            kf.compile(provider=StaticCompletionProvider())

    def test_compile_requires_provider(self, kf: KnowledgeFramework) -> None:
        with pytest.raises(RuntimeError, match="CompletionProvider"):
            kf.compile()

    def test_compile_empty_queue_no_episodes(self, kf: KnowledgeFramework) -> None:
        provider = StaticCompletionProvider(default="[]")
        result = kf.compile(provider=provider)
        assert result["episodes_processed"] == 0
        assert result["facts_extracted"] == 0

    def test_source_episode_recorded_on_staged_fact(self, kf: KnowledgeFramework) -> None:
        session_id = _seed_episode(kf, agent="ezra")
        provider = _json_provider(
            {"fact": "Use SQLite for Circle 4.", "confidence": 0.85}
        )
        kf.compile(provider=provider)
        queue = kf.get_curation_queue()
        assert queue[0]["source_episode"] == session_id
        assert queue[0]["source_agent"] == "ezra"


# ─── REST: POST /v1/compile ──────────────────────────────────────


class TestCompileEndpoint:
    def test_compile_without_provider_returns_422(self, config: KnowledgeConfig) -> None:
        app = create_app(config)
        client = TestClient(app)
        r = client.post("/v1/compile")
        assert r.status_code == 422

    def test_compile_without_circle4_returns_422(self, tmp_path: Path) -> None:
        config = KnowledgeConfig(
            circle1_path=tmp_path / "anamnesis.md",
            circle2_root=tmp_path / "boluses",
        )
        app = create_app(config)
        client = TestClient(app)
        r = client.post("/v1/compile")
        assert r.status_code == 422


# ─── Config: completion_provider in YAML ─────────────────────────


class TestCompletionProviderConfig:
    def test_openai_compat_provider_built_from_config(self, tmp_path: Path) -> None:
        from anamnesis.completion.openai_compat import OpenAICompatibleProvider

        config = KnowledgeConfig(
            circle1_path=tmp_path / "anamnesis.md",
            circle2_root=tmp_path / "boluses",
            completion_provider_type="openai_compatible",
            completion_provider_base_url="http://localhost:11434/v1",
            completion_provider_model="gemma4:26b",
        )
        kf = KnowledgeFramework(config)
        assert isinstance(kf._completion_provider, OpenAICompatibleProvider)
        assert kf._completion_provider.model == "gemma4:26b"

    def test_no_provider_type_gives_none(self, tmp_path: Path) -> None:
        config = KnowledgeConfig(
            circle1_path=tmp_path / "anamnesis.md",
            circle2_root=tmp_path / "boluses",
        )
        kf = KnowledgeFramework(config)
        assert kf._completion_provider is None

    def test_config_loader_flattens_completion_provider(self, tmp_path: Path) -> None:
        import yaml
        cfg_file = tmp_path / "anamnesis.yaml"
        cfg_file.write_text(yaml.dump({
            "circle1_path": str(tmp_path / "anamnesis.md"),
            "circle2_root": str(tmp_path / "boluses"),
            "completion_provider": {
                "type": "openai_compatible",
                "base_url": "http://localhost:11434/v1",
                "model": "gemma4:26b",
                "api_key": None,
            }
        }))
        from anamnesis.api.config_loader import load_config
        config = load_config(cfg_file)
        assert config.completion_provider_type == "openai_compatible"
        assert config.completion_provider_base_url == "http://localhost:11434/v1"
        assert config.completion_provider_model == "gemma4:26b"
