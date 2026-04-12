"""Tests for Circle 4 episode capture and storage."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from anamnesis import KnowledgeConfig, KnowledgeFramework
from anamnesis.episode.model import Episode, Turn
from anamnesis.episode.store import EpisodeStore


# ─── EpisodeStore (SQLite) ────────────────────────────────────────


@pytest.fixture
def store(tmp_path: Path) -> EpisodeStore:
    return EpisodeStore(tmp_path / "anamnesis.db")


def _make_episode(session_id="test-session", agent=None, n_turns=3, summary=None) -> Episode:
    now = datetime.now(timezone.utc)
    turns = [
        Turn(role="user" if i % 2 == 0 else "assistant",
             content=f"Turn {i} content",
             timestamp=(now + timedelta(seconds=i)).isoformat(),
             sequence=i)
        for i in range(n_turns)
    ]
    return Episode(
        session_id=session_id,
        agent=agent,
        started=now.isoformat(),
        ended=(now + timedelta(minutes=5)).isoformat(),
        turns=turns,
        summary=summary,
        turn_count=n_turns,
    )


class TestEpisodeStore:
    def test_save_and_load(self, store: EpisodeStore) -> None:
        ep = _make_episode()
        store.save(ep)
        loaded = store.load("test-session")
        assert loaded.session_id == "test-session"
        assert loaded.turn_count == 3
        assert len(loaded.turns) == 3
        assert loaded.turns[0].role == "user"
        assert loaded.turns[1].role == "assistant"

    def test_load_not_found(self, store: EpisodeStore) -> None:
        with pytest.raises(KeyError):
            store.load("nonexistent")

    def test_list(self, store: EpisodeStore) -> None:
        store.save(_make_episode("s1"))
        store.save(_make_episode("s2"))
        episodes = store.list()
        assert len(episodes) == 2
        # Metadata only — no turns
        assert "turns" not in episodes[0]
        assert episodes[0]["turn_count"] == 3

    def test_list_filter_by_agent(self, store: EpisodeStore) -> None:
        store.save(_make_episode("s1", agent="atlas"))
        store.save(_make_episode("s2", agent="selah"))
        store.save(_make_episode("s3", agent="atlas"))
        atlas_eps = store.list(agent="atlas")
        assert len(atlas_eps) == 2
        selah_eps = store.list(agent="selah")
        assert len(selah_eps) == 1

    def test_get_latest(self, store: EpisodeStore) -> None:
        store.save(_make_episode("s1"))
        store.save(_make_episode("s2"))
        latest = store.get_latest()
        assert latest is not None
        # s2 should be latest (inserted second, same started time but listed by desc)
        assert latest.session_id in ("s1", "s2")

    def test_get_latest_by_agent(self, store: EpisodeStore) -> None:
        store.save(_make_episode("s1", agent="atlas"))
        store.save(_make_episode("s2", agent="selah"))
        latest = store.get_latest(agent="atlas")
        assert latest is not None
        assert latest.agent == "atlas"

    def test_get_latest_empty(self, store: EpisodeStore) -> None:
        assert store.get_latest() is None

    def test_cleanup(self, store: EpisodeStore) -> None:
        old = _make_episode("old")
        old.ended = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
        store.save(old)

        recent = _make_episode("recent")
        store.save(recent)

        deleted = store.cleanup(retention_days=30)
        assert deleted == 1
        assert len(store.list()) == 1
        assert store.list()[0]["session_id"] == "recent"

    def test_cleanup_cascades_turns(self, store: EpisodeStore) -> None:
        old = _make_episode("old", n_turns=5)
        old.ended = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
        store.save(old)

        store.cleanup(retention_days=30)
        # Turns should be gone too
        with pytest.raises(KeyError):
            store.load("old")

    def test_compiled_defaults_false(self, store: EpisodeStore) -> None:
        store.save(_make_episode("s1"))
        loaded = store.load("s1")
        assert loaded.compiled is False

    def test_summary_stored(self, store: EpisodeStore) -> None:
        store.save(_make_episode("s1", summary="Worked on Anamnesis S01."))
        loaded = store.load("s1")
        assert loaded.summary == "Worked on Anamnesis S01."

    def test_db_created_automatically(self, tmp_path: Path) -> None:
        db_path = tmp_path / "subdir" / "anamnesis.db"
        store = EpisodeStore(db_path)
        assert db_path.exists()
        store.close()

    def test_turn_sequence_order(self, store: EpisodeStore) -> None:
        store.save(_make_episode("s1", n_turns=5))
        loaded = store.load("s1")
        sequences = [t.sequence for t in loaded.turns]
        assert sequences == [0, 1, 2, 3, 4]


# ─── KnowledgeFramework episode methods ──────────────────────────


@pytest.fixture
def kf(tmp_path: Path) -> KnowledgeFramework:
    cfg = KnowledgeConfig(
        circle1_path=tmp_path / "anamnesis.md",
        circle2_root=tmp_path / "boluses",
        circle4_root=tmp_path / "episodes",
    )
    return KnowledgeFramework(cfg)


@pytest.fixture
def kf_no_c4(tmp_path: Path) -> KnowledgeFramework:
    """Framework with Circle 4 disabled."""
    cfg = KnowledgeConfig(
        circle1_path=tmp_path / "anamnesis.md",
        circle2_root=tmp_path / "boluses",
    )
    return KnowledgeFramework(cfg)


class TestFrameworkEpisode:
    def test_capture_and_end(self, kf: KnowledgeFramework) -> None:
        kf.capture_turn("user", "Hello")
        kf.capture_turn("assistant", "Hi there")
        session_id = kf.end_session()
        assert session_id is not None

        episodes = kf.list_episodes()
        assert len(episodes) == 1
        assert episodes[0]["turn_count"] == 2

    def test_end_session_with_summary(self, kf: KnowledgeFramework) -> None:
        kf.capture_turn("user", "Let's work on S01")
        session_id = kf.end_session(summary="Completed scaffolding.")
        ep = kf.get_episode(session_id)
        assert ep.summary == "Completed scaffolding."

    def test_end_session_with_agent(self, kf: KnowledgeFramework) -> None:
        kf.capture_turn("user", "Hello Atlas")
        session_id = kf.end_session(agent="atlas")
        ep = kf.get_episode(session_id)
        assert ep.agent == "atlas"

    def test_end_session_no_turns_returns_none(self, kf: KnowledgeFramework) -> None:
        result = kf.end_session()
        assert result is None

    def test_capture_resets_after_end(self, kf: KnowledgeFramework) -> None:
        kf.capture_turn("user", "Session 1")
        kf.end_session()
        kf.capture_turn("user", "Session 2")
        session_id = kf.end_session()
        ep = kf.get_episode(session_id)
        assert ep.turn_count == 1
        assert ep.turns[0].content == "Session 2"

    def test_circle4_disabled_noop(self, kf_no_c4: KnowledgeFramework) -> None:
        kf_no_c4.capture_turn("user", "This goes nowhere")
        result = kf_no_c4.end_session()
        assert result is None
        assert kf_no_c4.list_episodes() == []

    def test_retention_cleanup(self, tmp_path: Path) -> None:
        cfg = KnowledgeConfig(
            circle1_path=tmp_path / "anamnesis.md",
            circle2_root=tmp_path / "boluses",
            circle4_root=tmp_path / "episodes",
            circle4_retention_days=30,
        )
        kf = KnowledgeFramework(cfg)

        # Manually insert an old episode
        from anamnesis.episode.model import Episode
        old = _make_episode("old-session")
        old.ended = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
        kf._episode_store.save(old)

        # Capture a new session — cleanup should run on end_session
        kf.capture_turn("user", "New session")
        kf.end_session()

        episodes = kf.list_episodes()
        ids = [e["session_id"] for e in episodes]
        assert "old-session" not in ids

    def test_list_episodes_filter_agent(self, kf: KnowledgeFramework) -> None:
        kf.capture_turn("user", "Atlas session")
        kf.end_session(agent="atlas")
        kf.capture_turn("user", "Selah session")
        kf.end_session(agent="selah")

        atlas = kf.list_episodes(agent="atlas")
        assert len(atlas) == 1
        assert atlas[0]["agent"] == "atlas"


# ─── REST API episode endpoints ──────────────────────────────────


@pytest.fixture
def episode_client(tmp_path: Path):
    from fastapi.testclient import TestClient
    from anamnesis.api.server import create_app

    cfg = KnowledgeConfig(
        circle1_path=tmp_path / "anamnesis.md",
        circle2_root=tmp_path / "boluses",
        circle4_root=tmp_path / "episodes",
    )
    app = create_app(cfg)
    return TestClient(app)


class TestEpisodeAPI:
    def test_capture_and_end(self, episode_client) -> None:
        r = episode_client.post("/v1/episodes/turn", json={"role": "user", "content": "Hello"})
        assert r.status_code == 200

        r = episode_client.post("/v1/episodes/turn", json={"role": "assistant", "content": "Hi"})
        assert r.status_code == 200

        r = episode_client.post("/v1/episodes/end", json={"summary": "Test session"})
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ended"
        assert data["session_id"] is not None

    def test_list_episodes(self, episode_client) -> None:
        episode_client.post("/v1/episodes/turn", json={"role": "user", "content": "Hello"})
        episode_client.post("/v1/episodes/end", json={})

        r = episode_client.get("/v1/episodes")
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_get_episode(self, episode_client) -> None:
        episode_client.post("/v1/episodes/turn", json={"role": "user", "content": "Hello"})
        r = episode_client.post("/v1/episodes/end", json={})
        session_id = r.json()["session_id"]

        r = episode_client.get(f"/v1/episodes/{session_id}")
        assert r.status_code == 200
        data = r.json()
        assert data["turn_count"] == 1
        assert len(data["turns"]) == 1
        assert data["turns"][0]["content"] == "Hello"

    def test_get_episode_not_found(self, episode_client) -> None:
        r = episode_client.get("/v1/episodes/nonexistent")
        assert r.status_code == 404

    def test_end_with_no_turns(self, episode_client) -> None:
        r = episode_client.post("/v1/episodes/end", json={})
        assert r.json()["status"] == "no_session"
