"""Extraction prompt template for the compilation pipeline."""

from __future__ import annotations

SYSTEM_PROMPT = """\
You are a knowledge extraction assistant. Your job is to read conversation \
transcripts and identify durable facts worth preserving in a long-term \
knowledge base. Extract only information that is genuinely worth remembering \
across future sessions — not transient details or implementation specifics \
already visible in code.\
"""

EXTRACTION_PROMPT_TEMPLATE = """\
Review the following conversation session and extract durable facts worth \
retaining long-term.

Good candidates:
- Decisions made explicitly (architecture choices, tooling preferences, policies)
- Patterns that worked well or should be avoided
- User preferences or constraints discovered
- Key dependencies, versions, or configuration facts
- Project-specific context not derivable from reading the code

Skip: debugging steps, obvious implementation details, transient status updates, \
anything that will be out of date quickly.

Existing knowledge boluses (suggest routing facts to these where appropriate):
{bolus_list}

Session ID: {session_id}
Agent: {agent}
Turns: {turn_count}

Transcript:
{transcript}

Return ONLY a JSON array. Each element: {{"fact": "...", "suggested_bolus": "...", \
"confidence": 0.0}}
Confidence: 0.9 = explicit decision, 0.8 = strong pattern, 0.6 = likely true, \
0.5 = worth flagging.
If no durable facts found, return an empty array: []
"""


def build_prompt(
    session_id: str,
    agent: str | None,
    turns: list[dict],
    bolus_summaries: list[str],
) -> str:
    transcript_lines = []
    for t in turns:
        role = t.get("role", "unknown")
        content = t.get("content", "")
        # Truncate very long turns to avoid blowing the context window
        if len(content) > 2000:
            content = content[:2000] + "... [truncated]"
        transcript_lines.append(f"{role}: {content}")

    return EXTRACTION_PROMPT_TEMPLATE.format(
        session_id=session_id,
        agent=agent or "unknown",
        turn_count=len(turns),
        bolus_list="\n".join(f"- {s}" for s in bolus_summaries) or "(none configured)",
        transcript="\n".join(transcript_lines),
    )
