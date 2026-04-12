"""Tests for KnowledgeFramework."""

from pathlib import Path

from anamnesis import KnowledgeConfig, KnowledgeFramework
from anamnesis.bolus.store import MarkdownBolusStore


def test_framework_accepts_config(tmp_path: Path) -> None:
    cfg = KnowledgeConfig(
        circle1_path=tmp_path / "anamnesis.md",
        circle2_root=tmp_path / "boluses",
    )
    kf = KnowledgeFramework(cfg)
    assert kf.config is cfg


def test_framework_initializes_markdown_store(tmp_path: Path) -> None:
    cfg = KnowledgeConfig(
        circle1_path=tmp_path / "anamnesis.md",
        circle2_root=tmp_path / "boluses",
    )
    kf = KnowledgeFramework(cfg)
    assert isinstance(kf.store, MarkdownBolusStore)
    assert kf.store.root == tmp_path / "boluses"
