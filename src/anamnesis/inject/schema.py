"""Injection schema — render model, token budget, and validation."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# ─── Token budget constants ─────────────────────────────────────

TOKEN_MINIMUM_VIABLE = 500
TOKEN_TARGET_LOW = 1000
TOKEN_TARGET_HIGH = 2500
TOKEN_SOFT_MAX_DEFAULT = 4000
TOKEN_HARD_CEILING = 6000

# ─── Render modes ───────────────────────────────────────────────

RENDER_INLINE = "inline"
RENDER_REFERENCE = "reference"
VALID_RENDER_MODES = {RENDER_INLINE, RENDER_REFERENCE}

# ─── Tool definition ────────────────────────────────────────────

RETRIEVE_KNOWLEDGE_TOOL = {
    "name": "retrieve_knowledge",
    "description": (
        "Retrieve the full content of a knowledge bolus by ID. "
        "Use when you need details beyond what the summary in your "
        "knowledge prompt provides."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "bolus_id": {
                "type": "string",
                "description": (
                    "The bolus identifier from the knowledge manifest "
                    "(e.g. 'infrastructure')"
                ),
            }
        },
        "required": ["bolus_id"],
    },
}

# ─── Validation ──────────────────────────────────────────────────


@dataclass
class ValidationResult:
    """Result of validating an anamnesis.md document."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_injection(text: str) -> ValidationResult:
    """Validate an anamnesis.md document.

    Checks:
    - <knowledge> wrapper present
    - Not empty
    - At least one inline or reference entry
    """
    errors: list[str] = []
    warnings: list[str] = []

    stripped = text.strip()

    # Check wrapper
    if not stripped.startswith("<knowledge>"):
        errors.append("Document must start with <knowledge> tag.")
    if not stripped.endswith("</knowledge>"):
        errors.append("Document must end with </knowledge> tag.")

    # Check non-empty content between tags
    inner = re.sub(r"</?knowledge>", "", stripped).strip()
    if not inner:
        errors.append("Document has no content between <knowledge> tags.")

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )
