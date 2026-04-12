"""Tests for KnowledgeConfig."""

from pathlib import Path

import pytest

from anamnesis import KnowledgeConfig


class TestKnowledgeConfigDefaults:
    def test_required_fields_only(self, tmp_path: Path) -> None:
        cfg = KnowledgeConfig(
            circle1_path=tmp_path / "anamnesis.md",
            circle2_root=tmp_path / "boluses",
        )
        assert cfg.circle1_path == tmp_path / "anamnesis.md"
        assert cfg.circle2_root == tmp_path / "boluses"
        assert cfg.circle1_max_tokens == 4000
        assert cfg.bolus_store == "markdown"
        assert cfg.api_host == "127.0.0.1"
        assert cfg.api_port == 8741
        assert cfg.api_key is None

    def test_string_paths_coerced(self) -> None:
        cfg = KnowledgeConfig(
            circle1_path="/tmp/anamnesis.md",  # type: ignore[arg-type]
            circle2_root="/tmp/boluses",  # type: ignore[arg-type]
        )
        assert isinstance(cfg.circle1_path, Path)
        assert isinstance(cfg.circle2_root, Path)

    def test_custom_token_budget(self, tmp_path: Path) -> None:
        cfg = KnowledgeConfig(
            circle1_path=tmp_path / "a.md",
            circle2_root=tmp_path / "b",
            circle1_max_tokens=2000,
        )
        assert cfg.circle1_max_tokens == 2000


class TestKnowledgeConfigValidation:
    def test_token_budget_minimum(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="circle1_max_tokens must be >= 500"):
            KnowledgeConfig(
                circle1_path=tmp_path / "a.md",
                circle2_root=tmp_path / "b",
                circle1_max_tokens=100,
            )

    def test_invalid_bolus_store(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="bolus_store must be one of"):
            KnowledgeConfig(
                circle1_path=tmp_path / "a.md",
                circle2_root=tmp_path / "b",
                bolus_store="redis",
            )
