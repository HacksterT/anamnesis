"""Tests for the recency pipeline (Circle 4 → Circle 1)."""

import logging
from pathlib import Path

import pytest

from anamnesis import KnowledgeConfig, KnowledgeFramework
from anamnesis.completion.provider import StaticCompletionProvider
from anamnesis.recency.pipeline import RECENCY_BOLUS_ID, update_recency
from anamnesis.bolus.store import MarkdownBolusStore
from tests.helpers import make_episode as _make_episode


# ─── Pipeline unit tests ─────────────────────────────────────────


@pytest.fixture
def store(tmp_path: Path) -> MarkdownBolusStore:
    return MarkdownBolusStore(tmp_path / "boluses")


class TestUpdateRecency:
    def test_creates_recency_bolus(self, store: MarkdownBolusStore) -> None:
        ep = _make_episode()
        update_recency(store, ep, budget=200)
        assert store.exists(RECENCY_BOLUS_ID)
        meta = store.get_metadata(RECENCY_BOLUS_ID)
        assert meta["render"] == "inline"
        assert meta["priority"] == 25
        assert "_system" in meta["tags"]

    def test_overwrites_on_second_call(self, store: MarkdownBolusStore) -> None:
        update_recency(store, _make_episode(summary="First session"), budget=200)
        content1 = store.read(RECENCY_BOLUS_ID)

        update_recency(store, _make_episode(summary="Second session"), budget=200)
        content2 = store.read(RECENCY_BOLUS_ID)

        assert "Second session" in content2
        assert content1 != content2

    def test_zero_budget_deletes_bolus(self, store: MarkdownBolusStore) -> None:
        update_recency(store, _make_episode(), budget=200)
        assert store.exists(RECENCY_BOLUS_ID)

        update_recency(store, _make_episode(), budget=0)
        assert not store.exists(RECENCY_BOLUS_ID)

    def test_uses_provider_when_given(self, store: MarkdownBolusStore) -> None:
        provider = StaticCompletionProvider(default="LLM summary.")
        update_recency(store, _make_episode(), budget=200, provider=provider)
        content = store.read(RECENCY_BOLUS_ID)
        assert content == "LLM summary."

    def test_uses_heuristic_without_provider(self, store: MarkdownBolusStore) -> None:
        update_recency(store, _make_episode(), budget=200, provider=None)
        content = store.read(RECENCY_BOLUS_ID)
        assert "Last session" in content


# ─── Framework integration tests ──────────────────────────────────


@pytest.fixture
def kf_recency(tmp_path: Path) -> KnowledgeFramework:
    cfg = KnowledgeConfig(
        circle1_path=tmp_path / "anamnesis.md",
        circle2_root=tmp_path / "boluses",
        circle4_root=tmp_path / "episodes",
        recency_budget=400,
    )
    return KnowledgeFramework(cfg)


class TestFrameworkRecency:
    def test_end_session_creates_recency_bolus(self, kf_recency: KnowledgeFramework) -> None:
        kf_recency.capture_turn("user", "Hello")
        kf_recency.capture_turn("assistant", "Hi there")
        kf_recency.end_session()

        # Recency bolus should exist in the store
        assert kf_recency.store.exists(RECENCY_BOLUS_ID)

    def test_recency_in_injection(self, kf_recency: KnowledgeFramework) -> None:
        kf_recency.capture_turn("user", "Working on Anamnesis")
        kf_recency.capture_turn("assistant", "Let me help with that")
        kf_recency.end_session()

        injection = kf_recency.get_injection()
        assert "Last session" in injection

    def test_recency_excluded_from_list_boluses(self, kf_recency: KnowledgeFramework) -> None:
        kf_recency.capture_turn("user", "Hello")
        kf_recency.end_session()

        # Default list excludes system boluses
        boluses = kf_recency.list_boluses()
        ids = [b["id"] for b in boluses]
        assert RECENCY_BOLUS_ID not in ids

        # include_system shows them
        boluses = kf_recency.list_boluses(include_system=True)
        ids = [b["id"] for b in boluses]
        assert RECENCY_BOLUS_ID in ids

    def test_recency_cannot_be_deleted(self, kf_recency: KnowledgeFramework) -> None:
        kf_recency.capture_turn("user", "Hello")
        kf_recency.end_session()

        with pytest.raises(ValueError, match="Cannot delete system bolus"):
            kf_recency.delete_bolus(RECENCY_BOLUS_ID)

    def test_metrics_include_recency(self, kf_recency: KnowledgeFramework) -> None:
        kf_recency.capture_turn("user", "Hello")
        kf_recency.end_session()

        metrics = kf_recency.get_injection_metrics()
        assert "recency_tokens" in metrics
        assert metrics["recency_tokens"] > 0
        assert metrics["recency_budget"] == 400

    def test_zero_recency_budget_no_bolus(self, tmp_path: Path) -> None:
        cfg = KnowledgeConfig(
            circle1_path=tmp_path / "anamnesis.md",
            circle2_root=tmp_path / "boluses",
            circle4_root=tmp_path / "episodes",
            recency_budget=0,
        )
        kf = KnowledgeFramework(cfg)
        kf.capture_turn("user", "Hello")
        kf.end_session()

        assert not kf.store.exists(RECENCY_BOLUS_ID)

    def test_fifo_overwrites(self, kf_recency: KnowledgeFramework) -> None:
        kf_recency.capture_turn("user", "First session topic")
        kf_recency.end_session()
        content1 = kf_recency.store.read(RECENCY_BOLUS_ID)

        kf_recency.capture_turn("user", "Second session topic")
        kf_recency.end_session()
        content2 = kf_recency.store.read(RECENCY_BOLUS_ID)

        assert "Second session" in content2
        assert content1 != content2

    def test_end_to_end_injection_with_curated_and_recency(
        self, kf_recency: KnowledgeFramework
    ) -> None:
        # Create curated boluses
        kf_recency.create_bolus(
            "identity", "Physician-builder.",
            render="inline", priority=10, summary="Identity."
        )
        kf_recency.create_bolus(
            "infra", "Mac Mini M4 Pro.",
            summary="Servers.", tags=["tech"]
        )

        # Capture a session
        kf_recency.capture_turn("user", "Let's work on the API layer")
        kf_recency.capture_turn("assistant", "I'll implement the endpoints")
        kf_recency.end_session()

        # Get injection — should have all three: identity, recency, manifest
        injection = kf_recency.get_injection()
        assert "Physician-builder." in injection  # inline identity
        assert "Last session" in injection  # inline recency
        assert "-> `infra`" in injection  # reference manifest
