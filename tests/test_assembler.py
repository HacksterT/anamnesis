"""Tests for injection assembly and token budget."""

import logging
from pathlib import Path

import pytest

from anamnesis import KnowledgeConfig, KnowledgeFramework
from anamnesis.inject.assembler import assemble
from anamnesis.inject.budget import BudgetResult, SimpleTokenCounter, check_budget
from anamnesis.inject.schema import validate_injection
from anamnesis.bolus.store import MarkdownBolusStore


# ─── Token counting ─────────────────────────────────────────────


class TestSimpleTokenCounter:
    def test_empty_string(self) -> None:
        c = SimpleTokenCounter()
        assert c.count("") == 0

    def test_word_based_heuristic(self) -> None:
        c = SimpleTokenCounter()
        # 10 words * 1.3 = 13
        assert c.count("one two three four five six seven eight nine ten") == 13

    def test_prose_approximation(self) -> None:
        c = SimpleTokenCounter()
        text = "The quick brown fox jumps over the lazy dog."
        # 9 words * 1.3 = 11 (int)
        assert c.count(text) == 11


class TestBudgetCheck:
    def test_ok_status(self) -> None:
        result = check_budget("short text", SimpleTokenCounter(), soft_max=100)
        assert result.status == "ok"

    def test_warning_status(self) -> None:
        text = " ".join(["word"] * 3200)  # ~4160 tokens
        result = check_budget(text, SimpleTokenCounter(), soft_max=4000)
        assert result.status == "warning"

    def test_exceeded_status(self) -> None:
        text = " ".join(["word"] * 5000)  # ~6500 tokens
        result = check_budget(text, SimpleTokenCounter(), soft_max=4000, hard_ceiling=6000)
        assert result.status == "exceeded"

    def test_utilization_pct(self) -> None:
        result = BudgetResult(token_count=2000, soft_max=4000, hard_ceiling=6000, status="ok")
        assert result.utilization_pct == 50.0


# ─── Assembler ───────────────────────────────────────────────────


@pytest.fixture
def store(tmp_path: Path) -> MarkdownBolusStore:
    return MarkdownBolusStore(tmp_path / "boluses")


@pytest.fixture
def kf(tmp_path: Path) -> KnowledgeFramework:
    cfg = KnowledgeConfig(
        circle1_path=tmp_path / "anamnesis.md",
        circle2_root=tmp_path / "boluses",
    )
    return KnowledgeFramework(cfg)


def _write_bolus(store, bolus_id, content="content", **meta_overrides):
    """Helper to write a bolus with defaults."""
    meta = {
        "id": bolus_id,
        "title": bolus_id.replace("-", " ").title(),
        "active": True,
        "render": "reference",
        "priority": 50,
        "summary": f"Summary for {bolus_id}.",
    }
    meta.update(meta_overrides)
    store.write(bolus_id, content, meta)


class TestAssembler:
    def test_empty_store_produces_valid_document(self, store: MarkdownBolusStore) -> None:
        text, budget = assemble(store)
        assert text.startswith("<knowledge>")
        assert text.endswith("</knowledge>")

    def test_reference_boluses_in_manifest(self, store: MarkdownBolusStore) -> None:
        _write_bolus(store, "infra", summary="Mac Mini M4 Pro.")
        _write_bolus(store, "skills", summary="Python, TypeScript.")
        text, _ = assemble(store)
        assert "## Available Knowledge" in text
        assert "**Infra**: Mac Mini M4 Pro. -> `infra`" in text
        assert "**Skills**: Python, TypeScript. -> `skills`" in text

    def test_inline_boluses_rendered_as_prose(self, store: MarkdownBolusStore) -> None:
        _write_bolus(store, "identity", "Physician-builder. Solo operator.",
                     render="inline", priority=10)
        text, _ = assemble(store)
        assert "Physician-builder. Solo operator." in text
        # Inline boluses should NOT appear in manifest
        assert "-> `identity`" not in text

    def test_inline_before_reference(self, store: MarkdownBolusStore) -> None:
        _write_bolus(store, "identity", "I am the identity.",
                     render="inline", priority=10)
        _write_bolus(store, "infra", summary="Servers.")
        text, _ = assemble(store)
        identity_pos = text.index("I am the identity.")
        manifest_pos = text.index("## Available Knowledge")
        assert identity_pos < manifest_pos

    def test_inactive_boluses_excluded(self, store: MarkdownBolusStore) -> None:
        _write_bolus(store, "active-one", summary="Included.")
        _write_bolus(store, "inactive-one", summary="Excluded.", active=False)
        text, _ = assemble(store)
        assert "active-one" in text
        assert "inactive-one" not in text

    def test_priority_ordering(self, store: MarkdownBolusStore) -> None:
        _write_bolus(store, "constraints", "Do not hallucinate.",
                     render="inline", priority=90)
        _write_bolus(store, "identity", "Physician-builder.",
                     render="inline", priority=10)
        text, _ = assemble(store)
        id_pos = text.index("Physician-builder.")
        constraint_pos = text.index("Do not hallucinate.")
        assert id_pos < constraint_pos

    def test_validates_against_schema(self, store: MarkdownBolusStore) -> None:
        _write_bolus(store, "identity", "Test agent.", render="inline", priority=10)
        _write_bolus(store, "infra", summary="Servers.")
        text, _ = assemble(store)
        result = validate_injection(text)
        assert result.valid is True

    def test_hard_ceiling_raises(self, store: MarkdownBolusStore) -> None:
        # Create a bolus with enormous inline content
        big_content = " ".join(["word"] * 5000)
        _write_bolus(store, "huge", big_content, render="inline", priority=10)
        with pytest.raises(ValueError, match="hard ceiling"):
            assemble(store, hard_ceiling=6000)

    def test_soft_max_warns(self, store: MarkdownBolusStore, caplog) -> None:
        big_content = " ".join(["word"] * 3200)
        _write_bolus(store, "big", big_content, render="inline", priority=10)
        with caplog.at_level(logging.WARNING):
            text, budget = assemble(store, soft_max=4000)
        assert budget.status == "warning"
        assert "soft max" in caplog.text.lower()

    def test_manifest_line_format(self, store: MarkdownBolusStore) -> None:
        _write_bolus(store, "infrastructure",
                     summary="Mac Mini M4 Pro, macdevserver.",
                     title="Infrastructure")
        text, _ = assemble(store)
        assert "- **Infrastructure**: Mac Mini M4 Pro, macdevserver. -> `infrastructure`" in text


# ─── KnowledgeFramework injection methods ────────────────────────


class TestFrameworkInjection:
    def test_get_injection(self, kf: KnowledgeFramework) -> None:
        kf.create_bolus("identity", "Test agent.", render="inline",
                        priority=10, summary="Identity.")
        kf.create_bolus("infra", "Details.", summary="Servers.")
        text = kf.get_injection()
        assert "<knowledge>" in text
        assert "Test agent." in text
        assert "-> `infra`" in text

    def test_assemble_writes_file(self, kf: KnowledgeFramework) -> None:
        kf.create_bolus("identity", "Test agent.", render="inline",
                        priority=10, summary="Identity.")
        path = kf.assemble()
        assert path.exists()
        content = path.read_text()
        assert "<knowledge>" in content
        assert "Test agent." in content

    def test_get_injection_metrics(self, kf: KnowledgeFramework) -> None:
        kf.create_bolus("a", "content", summary="s")
        kf.create_bolus("b", "content", summary="s")
        kf.create_bolus("c", "content", summary="s")
        kf.set_bolus_active("c", False)
        metrics = kf.get_injection_metrics()
        assert metrics["active_boluses"] == 2
        assert metrics["total_boluses"] == 3
        assert metrics["status"] == "ok"
        assert "total_tokens" in metrics
        assert "utilization_pct" in metrics

    def test_retrieve_knowledge_flow(self, kf: KnowledgeFramework) -> None:
        """Simulate the full flow: get injection, see manifest, retrieve bolus."""
        kf.create_bolus("infra", "Mac Mini M4 Pro. 64GB RAM. macOS Sequoia.",
                        summary="Server details.", tags=["technical"])
        injection = kf.get_injection()
        # Agent sees the manifest
        assert "-> `infra`" in injection
        assert "Mac Mini M4 Pro. 64GB RAM." not in injection  # full content not inline
        # Agent calls retrieve_knowledge
        full_content = kf.retrieve("infra")
        assert "Mac Mini M4 Pro. 64GB RAM. macOS Sequoia." in full_content
