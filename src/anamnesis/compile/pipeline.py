"""Compilation pipeline orchestrator: Circle 4 → Circle 3."""

from __future__ import annotations

from dataclasses import dataclass, field

from anamnesis.completion.provider import CompletionProvider
from anamnesis.compile.extractor import extract_facts
from anamnesis.curation.store import CurationStore
from anamnesis.episode.store import EpisodeStore
from anamnesis.bolus.base import BolusStore


@dataclass
class CompileResult:
    episodes_processed: int = 0
    facts_extracted: int = 0
    errors: list[str] = field(default_factory=list)


def compile_episodes(
    episode_store: EpisodeStore,
    curation_store: CurationStore,
    bolus_store: BolusStore,
    provider: CompletionProvider,
    agent: str | None = None,
) -> CompileResult:
    """Extract facts from all uncompiled episodes and stage them in Circle 3.

    Processes episodes oldest-first. Each episode is marked compiled after
    successful extraction (even if zero facts were found — the episode was
    reviewed, just nothing was worth keeping).
    """
    result = CompileResult()

    session_ids = episode_store.list_uncompiled(agent=agent)
    if not session_ids:
        return result

    # Build bolus summary list for the extraction prompt
    bolus_summaries = _bolus_summary_lines(bolus_store)

    for session_id in session_ids:
        try:
            episode = episode_store.load(session_id)
            if not episode.turns:
                episode_store.mark_compiled(session_id)
                continue

            facts = extract_facts(episode, provider, bolus_summaries)

            for fact in facts:
                curation_store.stage(
                    fact.fact,
                    source_episode=session_id,
                    source_agent=episode.agent,
                    suggested_bolus=fact.suggested_bolus,
                    confidence=fact.confidence,
                )
                result.facts_extracted += 1

            episode_store.mark_compiled(session_id)
            result.episodes_processed += 1

        except Exception as exc:
            result.errors.append(f"{session_id}: {exc}")
            # Continue with next episode — don't let one failure stop the run

    return result


def _bolus_summary_lines(bolus_store: BolusStore) -> list[str]:
    """Build a compact bolus list for the extraction prompt."""
    boluses = bolus_store.list(active_only=False)
    lines = []
    for b in boluses:
        bolus_id = b.get("id", "")
        if bolus_id.startswith("_"):
            continue
        summary = b.get("summary", "")
        lines.append(f"{bolus_id}: {summary}" if summary else bolus_id)
    return lines
