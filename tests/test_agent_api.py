"""Tests for the Agent REST API endpoints."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from anamnesis.config import KnowledgeConfig
from anamnesis.api.server import create_app
from anamnesis.init import init_project


@pytest.fixture
def agent_client(tmp_path: Path, monkeypatch):
    """Client with a config file that supports agent operations."""
    monkeypatch.chdir(tmp_path)
    config_path = init_project(Path("knowledge"))

    cfg = KnowledgeConfig(
        circle1_path=tmp_path / "knowledge" / "anamnesis.md",
        circle2_root=tmp_path / "knowledge" / "boluses",
    )
    app = create_app(cfg, config_path=str(config_path))
    return TestClient(app)


class TestAgentAPI:
    def test_list_agents_empty(self, agent_client) -> None:
        r = agent_client.get("/v1/agents")
        assert r.status_code == 200
        assert r.json() == {}

    def test_create_agent(self, agent_client) -> None:
        r = agent_client.post("/v1/agents", json={
            "name": "atlas",
            "token_budget": 4000,
            "recency_budget": 500,
        })
        assert r.status_code == 201
        assert r.json()["name"] == "atlas"

        # Verify it exists
        r = agent_client.get("/v1/agents/atlas")
        assert r.status_code == 200
        data = r.json()
        assert data["token_budget"] == 4000
        assert data["recency_budget"] == 500

    def test_create_duplicate_agent(self, agent_client) -> None:
        agent_client.post("/v1/agents", json={"name": "atlas"})
        r = agent_client.post("/v1/agents", json={"name": "atlas"})
        assert r.status_code == 409

    def test_list_agents(self, agent_client) -> None:
        agent_client.post("/v1/agents", json={"name": "atlas"})
        agent_client.post("/v1/agents", json={"name": "selah", "recency_budget": 200})

        r = agent_client.get("/v1/agents")
        data = r.json()
        assert "atlas" in data
        assert "selah" in data
        assert data["selah"]["recency_budget"] == 200

    def test_update_agent_partial(self, agent_client) -> None:
        agent_client.post("/v1/agents", json={"name": "atlas", "recency_budget": 400})

        # Update only recency_budget
        r = agent_client.patch("/v1/agents/atlas", json={"recency_budget": 600})
        assert r.status_code == 200
        data = r.json()
        assert data["recency_budget"] == 600
        assert data["token_budget"] == 4000  # Preserved

    def test_update_agent_not_found(self, agent_client) -> None:
        r = agent_client.patch("/v1/agents/nonexistent", json={"recency_budget": 100})
        assert r.status_code == 404

    def test_delete_agent(self, agent_client) -> None:
        agent_client.post("/v1/agents", json={"name": "atlas"})
        r = agent_client.delete("/v1/agents/atlas")
        assert r.status_code == 200

        r = agent_client.get("/v1/agents/atlas")
        assert r.status_code == 404

    def test_delete_agent_not_found(self, agent_client) -> None:
        r = agent_client.delete("/v1/agents/nonexistent")
        assert r.status_code == 404

    def test_get_agent_not_found(self, agent_client) -> None:
        r = agent_client.get("/v1/agents/nonexistent")
        assert r.status_code == 404

    def test_crud_lifecycle(self, agent_client) -> None:
        """Full create → read → update → delete lifecycle."""
        # Create
        agent_client.post("/v1/agents", json={
            "name": "selah", "token_budget": 3000, "recency_budget": 200
        })

        # Read
        r = agent_client.get("/v1/agents/selah")
        assert r.json()["token_budget"] == 3000

        # Update
        agent_client.patch("/v1/agents/selah", json={"token_budget": 3500})
        r = agent_client.get("/v1/agents/selah")
        assert r.json()["token_budget"] == 3500

        # Delete
        r = agent_client.delete("/v1/agents/selah")
        assert r.status_code == 200
        r = agent_client.get("/v1/agents")
        assert "selah" not in r.json()
