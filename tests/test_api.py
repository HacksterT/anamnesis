"""Tests for the REST API layer."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from anamnesis.config import KnowledgeConfig
from anamnesis.api.server import create_app


@pytest.fixture
def config(tmp_path: Path) -> KnowledgeConfig:
    return KnowledgeConfig(
        circle1_path=tmp_path / "anamnesis.md",
        circle2_root=tmp_path / "boluses",
    )


@pytest.fixture
def client(config: KnowledgeConfig) -> TestClient:
    app = create_app(config)
    return TestClient(app)


@pytest.fixture
def seeded_client(config: KnowledgeConfig) -> TestClient:
    """Client with some boluses pre-created."""
    from anamnesis.framework import KnowledgeFramework
    kf = KnowledgeFramework(config)
    kf.create_bolus("identity", "Physician-builder. Solo operator.",
                    render="inline", priority=10, summary="User identity.")
    kf.create_bolus("infra", "Mac Mini M4 Pro. 64GB RAM.",
                    summary="Server details.", tags=["technical"])
    kf.create_bolus("inactive-one", "Old stuff.",
                    summary="Deprecated.", tags=["archive"])
    kf.set_bolus_active("inactive-one", False)

    app = create_app(config)
    return TestClient(app)


# ─── Health ──────────────────────────────────────────────────────


def test_health(client: TestClient) -> None:
    r = client.get("/v1/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


# ─── Injection ───────────────────────────────────────────────────


def test_get_injection_empty(client: TestClient) -> None:
    r = client.get("/v1/knowledge/injection")
    assert r.status_code == 200
    assert "<knowledge>" in r.text


def test_get_injection_with_boluses(seeded_client: TestClient) -> None:
    r = seeded_client.get("/v1/knowledge/injection")
    assert r.status_code == 200
    assert "Physician-builder" in r.text
    assert "-> `infra`" in r.text
    assert "inactive-one" not in r.text


def test_get_injection_metrics(seeded_client: TestClient) -> None:
    r = seeded_client.get("/v1/knowledge/injection/metrics")
    assert r.status_code == 200
    data = r.json()
    assert data["active_boluses"] == 2
    assert data["total_boluses"] == 3
    assert "total_tokens" in data
    assert "utilization_pct" in data


# ─── Bolus CRUD ──────────────────────────────────────────────────


def test_list_boluses(seeded_client: TestClient) -> None:
    r = seeded_client.get("/v1/knowledge/boluses")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2  # active only by default

    r = seeded_client.get("/v1/knowledge/boluses?active_only=false")
    assert len(r.json()) == 3


def test_get_bolus(seeded_client: TestClient) -> None:
    r = seeded_client.get("/v1/knowledge/boluses/infra")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == "infra"
    assert "Mac Mini" in data["content"]
    assert data["metadata"]["render"] == "reference"


def test_get_bolus_not_found(client: TestClient) -> None:
    r = client.get("/v1/knowledge/boluses/nonexistent")
    assert r.status_code == 404


def test_create_bolus(client: TestClient) -> None:
    r = client.post("/v1/knowledge/boluses", json={
        "id": "new-bolus",
        "title": "New Bolus",
        "summary": "A new test bolus.",
        "content": "Some content here.",
        "render": "reference",
        "tags": ["test"],
    })
    assert r.status_code == 201
    assert r.json()["id"] == "new-bolus"

    # Verify it exists
    r = client.get("/v1/knowledge/boluses/new-bolus")
    assert r.status_code == 200
    assert "Some content here." in r.json()["content"]


def test_create_duplicate_bolus(seeded_client: TestClient) -> None:
    r = seeded_client.post("/v1/knowledge/boluses", json={
        "id": "infra",
        "summary": "duplicate",
        "content": "x",
    })
    assert r.status_code == 409


def test_update_bolus(seeded_client: TestClient) -> None:
    r = seeded_client.put("/v1/knowledge/boluses/infra", json={
        "content": "Updated content here.",
    })
    assert r.status_code == 200

    r = seeded_client.get("/v1/knowledge/boluses/infra")
    assert "Updated content here." in r.json()["content"]


def test_update_bolus_not_found(client: TestClient) -> None:
    r = client.put("/v1/knowledge/boluses/nonexistent", json={"content": "x"})
    assert r.status_code == 404


def test_delete_bolus(seeded_client: TestClient) -> None:
    r = seeded_client.delete("/v1/knowledge/boluses/infra")
    assert r.status_code == 200

    r = seeded_client.get("/v1/knowledge/boluses/infra")
    assert r.status_code == 404


def test_delete_bolus_not_found(client: TestClient) -> None:
    r = client.delete("/v1/knowledge/boluses/nonexistent")
    assert r.status_code == 404


def test_activate_deactivate(seeded_client: TestClient) -> None:
    # Deactivate
    r = seeded_client.patch("/v1/knowledge/boluses/infra/deactivate")
    assert r.status_code == 200
    assert r.json()["active"] is False

    # Should no longer appear in active-only list
    r = seeded_client.get("/v1/knowledge/boluses")
    ids = [b["id"] for b in r.json()]
    assert "infra" not in ids

    # Reactivate
    r = seeded_client.patch("/v1/knowledge/boluses/infra/activate")
    assert r.status_code == 200
    assert r.json()["active"] is True


def test_activate_not_found(client: TestClient) -> None:
    r = client.patch("/v1/knowledge/boluses/nonexistent/activate")
    assert r.status_code == 404


# ─── Retrieve knowledge (tool endpoint) ──────────────────────────


def test_retrieve_knowledge(seeded_client: TestClient) -> None:
    r = seeded_client.get("/v1/knowledge/retrieve/infra")
    assert r.status_code == 200
    assert "Mac Mini" in r.text


def test_retrieve_knowledge_not_found(client: TestClient) -> None:
    r = client.get("/v1/knowledge/retrieve/nonexistent")
    assert r.status_code == 404


# ─── API key auth ─────────────────────────────────────────────────


def test_auth_required_when_configured(tmp_path: Path) -> None:
    config = KnowledgeConfig(
        circle1_path=tmp_path / "anamnesis.md",
        circle2_root=tmp_path / "boluses",
        api_key="test-secret-key",
    )
    app = create_app(config)
    client = TestClient(app)

    # No auth → 401
    r = client.get("/v1/knowledge/boluses")
    assert r.status_code == 401

    # Wrong key → 401
    r = client.get("/v1/knowledge/boluses",
                   headers={"Authorization": "Bearer wrong-key"})
    assert r.status_code == 401

    # Correct key → 200
    r = client.get("/v1/knowledge/boluses",
                   headers={"Authorization": "Bearer test-secret-key"})
    assert r.status_code == 200

    # Health endpoint skips auth
    r = client.get("/v1/health")
    assert r.status_code == 200


def test_no_auth_when_not_configured(client: TestClient) -> None:
    r = client.get("/v1/knowledge/boluses")
    assert r.status_code == 200
