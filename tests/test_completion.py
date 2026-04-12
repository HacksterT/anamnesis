"""Tests for CompletionProvider protocol and summarization."""

import pytest

from anamnesis.completion.heuristic import HeuristicSummarizer
from anamnesis.completion.provider import CompletionProvider, StaticCompletionProvider
from anamnesis.completion.summarizer import summarize_episode
from anamnesis.inject.budget import SimpleTokenCounter
from tests.helpers import make_episode as _make_episode


# ─── Protocol ────────────────────────────────────────────────────


class TestCompletionProviderProtocol:
    def test_static_provider_is_protocol_compliant(self) -> None:
        p = StaticCompletionProvider()
        assert isinstance(p, CompletionProvider)

    def test_static_provider_default_response(self) -> None:
        p = StaticCompletionProvider()
        result = p.complete("anything")
        assert "Static summary" in result

    def test_static_provider_matching_response(self) -> None:
        p = StaticCompletionProvider(
            responses={"Anamnesis": "Working on knowledge framework."}
        )
        result = p.complete("Session about Anamnesis S01")
        assert result == "Working on knowledge framework."

    def test_static_provider_no_match_returns_default(self) -> None:
        p = StaticCompletionProvider(
            responses={"specific": "matched"},
            default="fallback",
        )
        result = p.complete("nothing matches here")
        assert result == "fallback"


# ─── Heuristic summarizer ────────────────────────────────────────


class TestHeuristicSummarizer:
    def test_produces_output_within_budget(self) -> None:
        h = HeuristicSummarizer()
        counter = SimpleTokenCounter()
        ep = _make_episode(n_turns=20)
        result = h.summarize(ep, budget=100)
        assert counter.count(result) <= 100

    def test_single_turn_episode(self) -> None:
        ep = _make_episode(n_turns=1)
        h = HeuristicSummarizer()
        result = h.summarize(ep, budget=200)
        assert "Turn 0 content" in result

    def test_large_episode_takes_last_turns(self) -> None:
        ep = _make_episode(n_turns=50)
        h = HeuristicSummarizer()
        result = h.summarize(ep, budget=100)
        # Should contain later turns, not earlier ones
        assert "Last session" in result

    def test_empty_episode(self) -> None:
        ep = _make_episode(n_turns=0)
        h = HeuristicSummarizer()
        result = h.summarize(ep, budget=100)
        assert result == ""

    def test_uses_human_summary_if_present(self) -> None:
        ep = _make_episode(n_turns=5, summary="Completed the scaffolding story.")
        h = HeuristicSummarizer()
        result = h.summarize(ep, budget=200)
        assert "Completed the scaffolding story." in result

    def test_truncates_long_human_summary(self) -> None:
        long_summary = " ".join(["word"] * 200)
        ep = _make_episode(n_turns=1, summary=long_summary)
        h = HeuristicSummarizer()
        counter = SimpleTokenCounter()
        result = h.summarize(ep, budget=50)
        assert counter.count(result) <= 50

    def test_very_small_budget(self) -> None:
        ep = _make_episode(n_turns=5)
        h = HeuristicSummarizer()
        counter = SimpleTokenCounter()
        result = h.summarize(ep, budget=10)
        assert counter.count(result) <= 10


# ─── Summarize orchestrator ──────────────────────────────────────


class TestSummarizeEpisode:
    def test_uses_provider_when_available(self) -> None:
        provider = StaticCompletionProvider(default="LLM summary here.")
        ep = _make_episode()
        result = summarize_episode(ep, budget=200, provider=provider)
        assert result == "LLM summary here."

    def test_falls_back_to_heuristic(self) -> None:
        ep = _make_episode()
        result = summarize_episode(ep, budget=200, provider=None)
        assert "Last session" in result

    def test_truncates_provider_output(self) -> None:
        # Provider returns way too much
        long_response = " ".join(["word"] * 500)
        provider = StaticCompletionProvider(default=long_response)
        counter = SimpleTokenCounter()
        ep = _make_episode()
        result = summarize_episode(ep, budget=50, provider=provider, counter=counter)
        assert counter.count(result) <= 50

    def test_heuristic_respects_budget(self) -> None:
        counter = SimpleTokenCounter()
        ep = _make_episode(n_turns=30)
        result = summarize_episode(ep, budget=80, provider=None, counter=counter)
        assert counter.count(result) <= 80
