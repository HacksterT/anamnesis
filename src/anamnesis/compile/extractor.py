"""Single-episode fact extraction."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from anamnesis.completion.provider import CompletionProvider
from anamnesis.compile.prompts import SYSTEM_PROMPT, build_prompt
from anamnesis.episode.model import Episode


@dataclass
class ExtractedFact:
    fact: str
    suggested_bolus: str | None
    confidence: float


def extract_facts(
    episode: Episode,
    provider: CompletionProvider,
    bolus_summaries: list[str] | None = None,
) -> list[ExtractedFact]:
    """Extract durable facts from an episode using the LLM.

    Returns an empty list (not an error) if the LLM finds nothing worth keeping
    or if its output cannot be parsed.
    """
    turns = [
        {"role": t.role, "content": t.content}
        for t in episode.turns
    ]

    prompt = build_prompt(
        session_id=episode.session_id,
        agent=episode.agent,
        turns=turns,
        bolus_summaries=bolus_summaries or [],
    )

    try:
        raw = provider.complete(prompt, system=SYSTEM_PROMPT)
    except Exception as exc:
        raise RuntimeError(
            f"LLM call failed for episode {episode.session_id}: {exc}"
        ) from exc

    return _parse_response(raw)


def _parse_response(raw: str) -> list[ExtractedFact]:
    """Parse LLM output into ExtractedFact list. Tolerant of common formatting issues."""
    text = raw.strip()

    # Strip markdown code fences if present
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    # Extract the first JSON array found in the text
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        return []

    try:
        items = json.loads(match.group())
    except json.JSONDecodeError:
        return []

    facts = []
    for item in items:
        if not isinstance(item, dict):
            continue
        fact_text = item.get("fact", "").strip()
        if not fact_text:
            continue
        facts.append(
            ExtractedFact(
                fact=fact_text,
                suggested_bolus=item.get("suggested_bolus") or None,
                confidence=float(item.get("confidence", 0.5)),
            )
        )
    return facts
