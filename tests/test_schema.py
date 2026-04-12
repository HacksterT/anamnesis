"""Tests for injection schema and validation."""

from anamnesis.inject.schema import (
    RENDER_INLINE,
    RENDER_REFERENCE,
    RETRIEVE_KNOWLEDGE_TOOL,
    TOKEN_HARD_CEILING,
    TOKEN_MINIMUM_VIABLE,
    TOKEN_SOFT_MAX_DEFAULT,
    TOKEN_TARGET_HIGH,
    TOKEN_TARGET_LOW,
    VALID_RENDER_MODES,
    validate_injection,
)

# ─── Reference examples ─────────────────────────────────────────

VALID_DOCUMENT = """\
<knowledge>
Physician-builder. Solo operator.

Prefer terse communication. Do not hallucinate credentials.

## Available Knowledge
- **Infrastructure**: Mac Mini M4 Pro. -> `infrastructure`
- **Technical Skills**: Python, TypeScript. -> `technical-skills`
</knowledge>"""

MINIMAL_VALID = """\
<knowledge>
A test agent with some orientation context.
</knowledge>"""


# ─── Render modes ────────────────────────────────────────────────


class TestRenderModes:
    def test_two_modes(self) -> None:
        assert VALID_RENDER_MODES == {"inline", "reference"}

    def test_constants(self) -> None:
        assert RENDER_INLINE == "inline"
        assert RENDER_REFERENCE == "reference"


# ─── Token constants ─────────────────────────────────────────────


class TestTokenConstants:
    def test_bounds_ordering(self) -> None:
        assert TOKEN_MINIMUM_VIABLE < TOKEN_TARGET_LOW
        assert TOKEN_TARGET_LOW < TOKEN_TARGET_HIGH
        assert TOKEN_TARGET_HIGH < TOKEN_SOFT_MAX_DEFAULT
        assert TOKEN_SOFT_MAX_DEFAULT < TOKEN_HARD_CEILING

    def test_specific_values(self) -> None:
        assert TOKEN_MINIMUM_VIABLE == 500
        assert TOKEN_TARGET_LOW == 1000
        assert TOKEN_TARGET_HIGH == 2500
        assert TOKEN_SOFT_MAX_DEFAULT == 4000
        assert TOKEN_HARD_CEILING == 6000


# ─── Tool definition ─────────────────────────────────────────────


class TestToolDefinition:
    def test_tool_name(self) -> None:
        assert RETRIEVE_KNOWLEDGE_TOOL["name"] == "retrieve_knowledge"

    def test_tool_has_bolus_id_parameter(self) -> None:
        props = RETRIEVE_KNOWLEDGE_TOOL["parameters"]["properties"]
        assert "bolus_id" in props
        assert props["bolus_id"]["type"] == "string"

    def test_bolus_id_is_required(self) -> None:
        assert "bolus_id" in RETRIEVE_KNOWLEDGE_TOOL["parameters"]["required"]


# ─── Validation ──────────────────────────────────────────────────


class TestValidation:
    def test_valid_full_document(self) -> None:
        result = validate_injection(VALID_DOCUMENT)
        assert result.valid is True
        assert result.errors == []

    def test_valid_minimal_document(self) -> None:
        result = validate_injection(MINIMAL_VALID)
        assert result.valid is True

    def test_missing_knowledge_wrapper(self) -> None:
        doc = "Just some text without wrapper."
        result = validate_injection(doc)
        assert result.valid is False
        assert any("<knowledge>" in e for e in result.errors)

    def test_missing_closing_wrapper(self) -> None:
        doc = "<knowledge>\nSome content here."
        result = validate_injection(doc)
        assert result.valid is False
        assert any("</knowledge>" in e for e in result.errors)

    def test_empty_content(self) -> None:
        doc = "<knowledge>\n</knowledge>"
        result = validate_injection(doc)
        assert result.valid is False
        assert any("no content" in e.lower() for e in result.errors)

    def test_whitespace_only_content(self) -> None:
        doc = "<knowledge>\n   \n  \n</knowledge>"
        result = validate_injection(doc)
        assert result.valid is False
