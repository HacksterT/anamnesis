"""Tests for BolusStore ABC and MarkdownBolusStore."""

from pathlib import Path

import pytest

from anamnesis import KnowledgeConfig, KnowledgeFramework
from anamnesis.bolus.base import BolusStore
from anamnesis.bolus.store import MarkdownBolusStore, validate_bolus_id, slugify
from anamnesis.bolus import frontmatter


# ─── ABC tests ──────────────────────────────────────────────────


def test_bolus_store_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        BolusStore()  # type: ignore[abstract]


def test_concrete_subclass_must_implement_all_methods() -> None:
    class IncompleteStore(BolusStore):
        def read(self, bolus_id: str) -> str:
            return ""

    with pytest.raises(TypeError):
        IncompleteStore()  # type: ignore[abstract]


# ─── ID validation ──────────────────────────────────────────────


class TestBolusIdValidation:
    def test_valid_slugs(self) -> None:
        assert validate_bolus_id("infrastructure") == "infrastructure"
        assert validate_bolus_id("my-bolus") == "my-bolus"
        assert validate_bolus_id("a1-b2-c3") == "a1-b2-c3"

    def test_invalid_slugs(self) -> None:
        for bad in ["My Bolus", "UPPER", "has_underscore", "has.dot", "", "trailing-", "-leading"]:
            with pytest.raises(ValueError):
                validate_bolus_id(bad)

    def test_slugify(self) -> None:
        assert slugify("My Bolus Name") == "my-bolus-name"
        assert slugify("Infrastructure & Systems") == "infrastructure-systems"
        assert slugify("  spaces  ") == "spaces"


# ─── Frontmatter round-trip ─────────────────────────────────────


class TestFrontmatter:
    def test_parse_and_dump_round_trip(self) -> None:
        meta = {"id": "test", "title": "Test", "active": True, "tags": ["a", "b"]}
        body = "Some content here.\n\nWith paragraphs."
        text = frontmatter.dump(meta, body)
        parsed_meta, parsed_body = frontmatter.parse(text)
        assert parsed_meta == meta
        assert parsed_body == body

    def test_parse_no_frontmatter(self) -> None:
        meta, body = frontmatter.parse("Just plain text.")
        assert meta == {}
        assert body == "Just plain text."

    def test_unknown_fields_preserved(self) -> None:
        meta = {"id": "x", "custom_field": 42, "nested": {"a": 1}}
        text = frontmatter.dump(meta, "body")
        parsed_meta, _ = frontmatter.parse(text)
        assert parsed_meta["custom_field"] == 42
        assert parsed_meta["nested"] == {"a": 1}


# ─── MarkdownBolusStore CRUD ────────────────────────────────────


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


class TestMarkdownBolusStore:
    def test_write_and_read(self, store: MarkdownBolusStore) -> None:
        store.write("infra", "Content here.", {
            "id": "infra", "title": "Infrastructure", "active": True,
            "summary": "Servers and stuff.", "tags": [],
        })
        body = store.read("infra")
        assert body == "Content here."

    def test_exists(self, store: MarkdownBolusStore) -> None:
        assert not store.exists("infra")
        store.write("infra", "x", {
            "id": "infra", "title": "Infra", "active": True,
            "summary": "s", "tags": [],
        })
        assert store.exists("infra")

    def test_delete(self, store: MarkdownBolusStore) -> None:
        store.write("infra", "x", {
            "id": "infra", "title": "Infra", "active": True,
            "summary": "s", "tags": [],
        })
        assert store.delete("infra") is True
        assert store.delete("infra") is False
        assert not store.exists("infra")

    def test_list_active_only(self, store: MarkdownBolusStore) -> None:
        store.write("a", "x", {"id": "a", "title": "A", "active": True, "summary": "s"})
        store.write("b", "x", {"id": "b", "title": "B", "active": False, "summary": "s"})
        active = store.list(active_only=True)
        assert len(active) == 1
        assert active[0]["id"] == "a"

        all_boluses = store.list(active_only=False)
        assert len(all_boluses) == 2

    def test_get_metadata(self, store: MarkdownBolusStore) -> None:
        store.write("infra", "body", {
            "id": "infra", "title": "Infrastructure", "active": True,
            "summary": "Mac Mini.", "tags": ["tech"],
        })
        meta = store.get_metadata("infra")
        assert meta["title"] == "Infrastructure"
        assert meta["tags"] == ["tech"]
        assert "created" in meta
        assert "updated" in meta

    def test_set_active(self, store: MarkdownBolusStore) -> None:
        store.write("infra", "body", {
            "id": "infra", "title": "Infra", "active": True, "summary": "s",
        })
        store.set_active("infra", False)
        meta = store.get_metadata("infra")
        assert meta["active"] is False

        store.set_active("infra", True)
        meta = store.get_metadata("infra")
        assert meta["active"] is True

    def test_read_nonexistent_raises(self, store: MarkdownBolusStore) -> None:
        with pytest.raises(KeyError):
            store.read("nope")

    def test_get_metadata_nonexistent_raises(self, store: MarkdownBolusStore) -> None:
        with pytest.raises(KeyError):
            store.get_metadata("nope")

    def test_set_active_nonexistent_raises(self, store: MarkdownBolusStore) -> None:
        with pytest.raises(KeyError):
            store.set_active("nope", True)

    def test_missing_required_fields_raises(self, store: MarkdownBolusStore) -> None:
        with pytest.raises(ValueError, match="missing required fields"):
            store.write("bad", "content", {"id": "bad"})

    def test_list_empty_dir(self, store: MarkdownBolusStore) -> None:
        assert store.list() == []

    def test_write_sets_timestamps(self, store: MarkdownBolusStore) -> None:
        store.write("infra", "body", {
            "id": "infra", "title": "Infra", "active": True, "summary": "s",
        })
        meta = store.get_metadata("infra")
        assert meta["created"] == meta["updated"]


# ─── KnowledgeFramework bolus methods ───────────────────────────


class TestFrameworkBolus:
    def test_create_and_read(self, kf: KnowledgeFramework) -> None:
        kf.create_bolus("infrastructure", "Mac Mini M4 Pro.", summary="Servers.")
        body = kf.read_bolus("infrastructure")
        assert "Mac Mini" in body

    def test_create_duplicate_raises(self, kf: KnowledgeFramework) -> None:
        kf.create_bolus("infrastructure", "content", summary="s")
        with pytest.raises(ValueError, match="already exists"):
            kf.create_bolus("infrastructure", "more content", summary="s")

    def test_update_preserves_metadata(self, kf: KnowledgeFramework) -> None:
        kf.create_bolus("infra", "old", summary="s", tags=["tech"])
        kf.update_bolus("infra", "new content")
        assert kf.read_bolus("infra") == "new content"
        meta = kf.get_bolus_metadata("infra")
        assert meta["tags"] == ["tech"]

    def test_delete(self, kf: KnowledgeFramework) -> None:
        kf.create_bolus("infra", "x", summary="s")
        assert kf.delete_bolus("infra") is True
        assert kf.delete_bolus("infra") is False

    def test_list_with_active_filter(self, kf: KnowledgeFramework) -> None:
        kf.create_bolus("a", "x", summary="s")
        kf.create_bolus("b", "x", summary="s")
        kf.set_bolus_active("b", False)
        assert len(kf.list_boluses()) == 1
        assert len(kf.list_boluses(active_only=False)) == 2

    def test_retrieve_alias(self, kf: KnowledgeFramework) -> None:
        kf.create_bolus("infra", "content here", summary="s")
        assert kf.retrieve("infra") == "content here"

    def test_create_with_tags(self, kf: KnowledgeFramework) -> None:
        kf.create_bolus("tech", "content", summary="s", tags=["technical"])
        meta = kf.get_bolus_metadata("tech")
        assert meta["tags"] == ["technical"]

    def test_create_auto_slugifies(self, kf: KnowledgeFramework) -> None:
        kf.create_bolus("My Infrastructure", "content", summary="s")
        assert kf.read_bolus("my-infrastructure") == "content"

    def test_file_is_human_readable(self, kf: KnowledgeFramework) -> None:
        kf.create_bolus("infra", "Mac Mini M4 Pro server.", summary="Servers.")
        path = kf.config.circle2_root / "infra.md"
        text = path.read_text()
        assert text.startswith("---\n")
        assert "Mac Mini M4 Pro server." in text
        assert "title:" in text
