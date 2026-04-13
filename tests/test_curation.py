"""Tests for F03-S03 + F04-S02: Circle 3 curation queue."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from anamnesis import KnowledgeConfig, KnowledgeFramework
from anamnesis.api.server import create_app


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


@pytest.fixture
def client(config: KnowledgeConfig) -> TestClient:
    app = create_app(config)
    return TestClient(app)


# ─── stage() ─────────────────────────────────────────────────────


class TestStage:
    def test_stage_returns_id(self, kf: KnowledgeFramework) -> None:
        item_id = kf.stage("The user prefers uv over pip.")
        assert isinstance(item_id, int)
        assert item_id > 0

    def test_stage_appears_in_queue(self, kf: KnowledgeFramework) -> None:
        kf.stage("Prefer FastAPI for REST APIs.", suggested_bolus="cto-knowledge", confidence=0.8)
        queue = kf.get_curation_queue()
        assert len(queue) == 1
        assert queue[0]["fact"] == "Prefer FastAPI for REST APIs."
        assert queue[0]["suggested_bolus"] == "cto-knowledge"
        assert queue[0]["confidence"] == 0.8
        assert queue[0]["status"] == "pending"

    def test_stage_with_source_agent_and_url(self, kf: KnowledgeFramework) -> None:
        kf.stage(
            "LangGraph supports multi-agent coordination.",
            source_agent="claude-code",
            source_url="https://example.com/langgraph",
            suggested_bolus="cto-knowledge",
            confidence=0.9,
        )
        queue = kf.get_curation_queue()
        assert queue[0]["source_agent"] == "claude-code"
        assert queue[0]["source_url"] == "https://example.com/langgraph"

    def test_queue_ordered_by_confidence_descending(self, kf: KnowledgeFramework) -> None:
        kf.stage("Low confidence fact.", confidence=0.3)
        kf.stage("High confidence fact.", confidence=0.9)
        kf.stage("Medium confidence fact.", confidence=0.6)
        queue = kf.get_curation_queue()
        confidences = [item["confidence"] for item in queue]
        assert confidences == sorted(confidences, reverse=True)

    def test_stage_requires_circle4(self, tmp_path: Path) -> None:
        config = KnowledgeConfig(
            circle1_path=tmp_path / "anamnesis.md",
            circle2_root=tmp_path / "boluses",
            # No circle4_root
        )
        kf = KnowledgeFramework(config)
        with pytest.raises(RuntimeError, match="Circle 3"):
            kf.stage("Some fact.")


# ─── confirm() ───────────────────────────────────────────────────


class TestConfirm:
    def test_confirm_creates_bolus_when_not_exists(self, kf: KnowledgeFramework) -> None:
        item_id = kf.stage("uv is the preferred package manager.", suggested_bolus="tooling")
        kf.confirm(item_id, "tooling")
        content = kf.read_bolus("tooling")
        assert "uv is the preferred package manager." in content

    def test_confirm_appends_to_existing_bolus(self, kf: KnowledgeFramework) -> None:
        kf.create_bolus("cto-knowledge", "Existing content.", summary="CTO knowledge.")
        item_id = kf.stage("FastAPI is preferred over Flask.", suggested_bolus="cto-knowledge")
        kf.confirm(item_id, "cto-knowledge")
        content = kf.read_bolus("cto-knowledge")
        assert "Existing content." in content
        assert "FastAPI is preferred over Flask." in content

    def test_confirm_marks_item_confirmed(self, kf: KnowledgeFramework) -> None:
        item_id = kf.stage("Some fact.", confidence=0.8)
        kf.confirm(item_id, "cto-knowledge")
        # Confirmed items should not appear in pending queue
        queue = kf.get_curation_queue()
        ids = [item["id"] for item in queue]
        assert item_id not in ids

    def test_confirm_unknown_id_raises(self, kf: KnowledgeFramework) -> None:
        with pytest.raises(KeyError):
            kf.confirm(9999, "some-bolus")


# ─── reject() / defer() ──────────────────────────────────────────


class TestRejectDefer:
    def test_reject_removes_from_pending(self, kf: KnowledgeFramework) -> None:
        item_id = kf.stage("Maybe worth keeping.")
        kf.reject(item_id)
        queue = kf.get_curation_queue()
        assert all(item["id"] != item_id for item in queue)

    def test_defer_keeps_item_but_removes_from_pending(self, kf: KnowledgeFramework) -> None:
        item_id = kf.stage("Come back to this later.")
        kf.defer(item_id)
        queue = kf.get_curation_queue()
        assert all(item["id"] != item_id for item in queue)


# ─── REST: GET /v1/curation ──────────────────────────────────────


class TestCurationEndpoints:
    def test_list_empty_queue(self, client: TestClient) -> None:
        r = client.get("/v1/curation")
        assert r.status_code == 200
        assert r.json() == []

    def test_stage_via_api(self, client: TestClient) -> None:
        r = client.post("/v1/curation", json={
            "fact": "The project uses uv for dependency management.",
            "suggested_bolus": "cto-knowledge",
            "confidence": 0.85,
            "agent": "claude-code",
        })
        assert r.status_code == 201
        data = r.json()
        assert "id" in data
        assert data["status"] == "staged"

    def test_staged_item_appears_in_list(self, client: TestClient) -> None:
        client.post("/v1/curation", json={
            "fact": "FastAPI is preferred over Flask.",
            "suggested_bolus": "cto-knowledge",
            "confidence": 0.8,
        })
        r = client.get("/v1/curation")
        assert r.status_code == 200
        items = r.json()
        assert len(items) == 1
        assert items[0]["fact"] == "FastAPI is preferred over Flask."

    def test_confirm_via_api(self, client: TestClient) -> None:
        post_r = client.post("/v1/curation", json={
            "fact": "Use pytest for testing.",
            "suggested_bolus": "cto-knowledge",
            "confidence": 0.9,
        })
        item_id = post_r.json()["id"]

        r = client.post(f"/v1/curation/{item_id}/confirm", json={"bolus_id": "cto-knowledge"})
        assert r.status_code == 200
        assert r.json()["status"] == "confirmed"

    def test_reject_via_api(self, client: TestClient) -> None:
        post_r = client.post("/v1/curation", json={"fact": "Not worth keeping."})
        item_id = post_r.json()["id"]

        r = client.post(f"/v1/curation/{item_id}/reject")
        assert r.status_code == 200
        assert r.json()["status"] == "rejected"

    def test_defer_via_api(self, client: TestClient) -> None:
        post_r = client.post("/v1/curation", json={"fact": "Come back to this."})
        item_id = post_r.json()["id"]

        r = client.post(f"/v1/curation/{item_id}/defer")
        assert r.status_code == 200
        assert r.json()["status"] == "deferred"

    def test_confirm_unknown_returns_404(self, client: TestClient) -> None:
        r = client.post("/v1/curation/9999/confirm", json={"bolus_id": "somewhere"})
        assert r.status_code == 404

    def test_stage_without_circle4_returns_422(self, tmp_path: Path) -> None:
        from anamnesis.config import KnowledgeConfig
        from anamnesis.api.server import create_app
        config = KnowledgeConfig(
            circle1_path=tmp_path / "anamnesis.md",
            circle2_root=tmp_path / "boluses",
        )
        app = create_app(config)
        c = TestClient(app)
        r = c.post("/v1/curation", json={"fact": "Some fact."})
        assert r.status_code == 422
