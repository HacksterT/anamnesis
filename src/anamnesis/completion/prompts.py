"""Default summarization prompt template."""

SUMMARIZE_SESSION = """Summarize this conversation session concisely. Focus on:
- What was being worked on
- Key decisions made
- Open questions or next steps

Keep the summary under {budget} tokens. Write in present tense, third person.

Session:
{turns}"""
