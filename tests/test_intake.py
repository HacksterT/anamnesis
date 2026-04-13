"""Tests for F04-S01: Bolus Upsert & Append (External Content Intake)."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from anamnesis.config import KnowledgeConfig
from anamnesis.api.server import create_app
from anamnesis import KnowledgeFramework


@pytest.fixture
def config(tmp_path: Path) -> KnowledgeConfig:
    return KnowledgeConfig(
        circle1_path=tmp_path / "anamnesis.md",
        circle2_root=tmp_path / "boluses",
    )


@pytest.fixture
def kf(config: KnowledgeConfig) -> KnowledgeFramework:
    return KnowledgeFramework(config)


@pytest.fixture
def client(config: KnowledgeConfig) -> TestClient:
    app = create_app(config)
    return TestClient(app)


# ─── upsert_bolus (library) ──────────────────────────────────────


class TestUpsertBolus:
    def test_creates_when_not_exists(self, kf: KnowledgeFramework) -> None:
        result = kf.upsert_bolus("ai-memory-research", "Initial content.")
        assert result == "created"
        assert kf.read_bolus("ai-memory-research") == "Initial content."

    def test_updates_content_when_exists(self, kf: KnowledgeFramework) -> None:
        kf.create_bolus("ai-memory-research", "First version.", title="AI Memory", summary="Research notes.")
        result = kf.upsert_bolus("ai-memory-research", "Second version.")
        assert result == "updated"
        assert kf.read_bolus("ai-memory-research") == "Second version."

    def test_preserves_metadata_on_update(self, kf: KnowledgeFramework) -> None:
        kf.create_bolus(
            "ai-memory-research",
            "First version.",
            title="AI Memory",
            summary="Research notes.",
            tags=["ai", "research"],
            priority=20,
        )
        kf.upsert_bolus("ai-memory-research", "Second version.")
        meta = kf.get_bolus_metadata("ai-memory-research")
        assert meta["title"] == "AI Memory"
        assert meta["summary"] == "Research notes."
        assert meta["tags"] == ["ai", "research"]
        assert meta["priority"] == 20

    def test_uses_metadata_on_create(self, kf: KnowledgeFramework) -> None:
        kf.upsert_bolus(
            "ai-memory-research",
            "Initial content.",
            title="AI Memory Research",
            summary="Curated notes on AI memory.",
            tags=["ai"],
            priority=30,
        )
        meta = kf.get_bolus_metadata("ai-memory-research")
        assert meta["title"] == "AI Memory Research"
        assert meta["summary"] == "Curated notes on AI memory."
        assert meta["tags"] == ["ai"]
        assert meta["priority"] == 30

    def test_default_metadata_on_create_no_kwargs(self, kf: KnowledgeFramework) -> None:
        kf.upsert_bolus("my-bolus", "Content.")
        meta = kf.get_bolus_metadata("my-bolus")
        assert meta["title"] == "My Bolus"  # slugify-derived
        assert meta["render"] == "reference"
        assert meta["priority"] == 50

    def test_metadata_kwargs_ignored_on_update(self, kf: KnowledgeFramework) -> None:
        kf.create_bolus("my-bolus", "First.", title="Original Title", summary="Original summary.")
        kf.upsert_bolus("my-bolus", "Second.", title="New Title", summary="New summary.")
        meta = kf.get_bolus_metadata("my-bolus")
        # Metadata supplied on upsert-update is ignored; original metadata preserved.
        assert meta["title"] == "Original Title"
        assert meta["summary"] == "Original summary."


# ─── append_bolus (library) ──────────────────────────────────────


class TestAppendBolus:
    def test_appends_with_default_separator(self, kf: KnowledgeFramework) -> None:
        kf.create_bolus("research", "Part one.", summary="Research.")
        kf.append_bolus("research", "Part two.")
        content = kf.read_bolus("research")
        assert "Part one." in content
        assert "Part two." in content
        assert "\n\n---\n\n" in content

    def test_appends_with_custom_separator(self, kf: KnowledgeFramework) -> None:
        kf.create_bolus("research", "Part one.", summary="Research.")
        kf.append_bolus("research", "Part two.", separator="\n\n## New Section\n\n")
        content = kf.read_bolus("research")
        assert "## New Section" in content

    def test_raises_key_error_on_missing_bolus(self, kf: KnowledgeFramework) -> None:
        with pytest.raises(KeyError):
            kf.append_bolus("nonexistent", "Content.")

    def test_preserves_metadata_on_append(self, kf: KnowledgeFramework) -> None:
        kf.create_bolus("research", "Part one.", title="Research", summary="Notes.", priority=15)
        kf.append_bolus("research", "Part two.")
        meta = kf.get_bolus_metadata("research")
        assert meta["title"] == "Research"
        assert meta["summary"] == "Notes."
        assert meta["priority"] == 15

    def test_empty_body_appends_without_leading_separator(self, kf: KnowledgeFramework) -> None:
        kf.create_bolus("research", "", summary="Research.")
        kf.append_bolus("research", "First real content.")
        content = kf.read_bolus("research")
        assert content == "First real content."


# ─── PUT /v1/knowledge/boluses/{id} (upsert) ─────────────────────


class TestUpsertEndpoint:
    def test_creates_bolus_returns_201(self, client: TestClient) -> None:
        r = client.put(
            "/v1/knowledge/boluses/ai-memory-research",
            json={"content": "Initial content.", "title": "AI Memory Research"},
        )
        assert r.status_code == 201
        assert r.json()["status"] == "created"

    def test_updates_bolus_returns_200(self, client: TestClient, config: KnowledgeConfig) -> None:
        kf = KnowledgeFramework(config)
        kf.create_bolus("ai-memory-research", "First.", summary="Notes.")

        app = create_app(config)
        client2 = TestClient(app)
        r = client2.put(
            "/v1/knowledge/boluses/ai-memory-research",
            json={"content": "Second version."},
        )
        assert r.status_code == 200
        assert r.json()["status"] == "updated"

    def test_unsluggable_bolus_id_returns_422(self, client: TestClient) -> None:
        # "---" cannot be slugified (all hyphens, no alphanumeric content)
        r = client.put(
            "/v1/knowledge/boluses/---",
            json={"content": "Content."},
        )
        assert r.status_code == 422


# ─── POST /v1/knowledge/boluses/{id}/append ──────────────────────


class TestAppendEndpoint:
    def test_appends_to_existing_bolus(self, client: TestClient, config: KnowledgeConfig) -> None:
        kf = KnowledgeFramework(config)
        kf.create_bolus("research", "Part one.", summary="Notes.")

        app = create_app(config)
        client2 = TestClient(app)
        r = client2.post(
            "/v1/knowledge/boluses/research/append",
            json={"content": "Part two."},
        )
        assert r.status_code == 200
        assert r.json()["status"] == "appended"

    def test_append_to_missing_bolus_returns_404(self, client: TestClient) -> None:
        r = client.post(
            "/v1/knowledge/boluses/nonexistent/append",
            json={"content": "Content."},
        )
        assert r.status_code == 404

    def test_custom_separator_accepted(self, client: TestClient, config: KnowledgeConfig) -> None:
        kf = KnowledgeFramework(config)
        kf.create_bolus("research", "Part one.", summary="Notes.")

        app = create_app(config)
        client2 = TestClient(app)
        r = client2.post(
            "/v1/knowledge/boluses/research/append",
            json={"content": "Part two.", "separator": "\n\n## Entry\n\n"},
        )
        assert r.status_code == 200
        content = kf.read_bolus("research")
        assert "## Entry" in content
