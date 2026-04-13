Review this coding session and extract candidate knowledge for the Anamnesis curation queue.

## Your job

You are performing a session compaction. Examine what was built and decided in this conversation, extract durable knowledge worth keeping long-term, and stage each item in the Anamnesis Circle 3 curation queue for human review. Nothing goes directly to Circle 2 — the user reviews and promotes items from the queue.

## Step 1: Gather context

Run these to understand what changed:

```bash
git log --oneline -15
git diff HEAD
git status
```

Also review the conversation: what problems were solved, what architectural decisions were made, what approaches were tried and succeeded or failed.

## Step 2: Extract candidate facts

Identify 3–8 items worth retaining long-term. Good candidates:

- **Architectural decisions** — "We chose X over Y because Z"
- **Technical patterns** — approaches that worked well in this codebase
- **Constraints discovered** — things that can't be done, or must be done a certain way
- **Key dependencies or conventions** — versions, configs, naming rules
- **Mistakes to avoid** — approaches that failed and why

Skip: implementation details that are already in the code, transient debugging steps, anything obvious from reading the files.

Each fact should be:
- **Declarative** — a statement, not a question or instruction
- **Concise** — 1–3 sentences
- **Durable** — still true and useful in a future session

## Step 3: Assign suggested boluses

For each fact, suggest the most appropriate target bolus. Common targets for a coding session:
- `cto-knowledge` — technical decisions, architecture, stack choices
- `{project-name}` — project-specific facts (use the repo name as bolus ID)
- A more specific bolus if it exists (check `anamnesis bolus list` if the server is running)

## Step 4: Stage each fact

For each fact, call the Anamnesis API. The server runs at `http://127.0.0.1:8741`.

```bash
curl -s -X POST http://127.0.0.1:8741/v1/curation \
  -H "Content-Type: application/json" \
  -d '{
    "fact": "FACT TEXT HERE",
    "suggested_bolus": "BOLUS_ID",
    "confidence": 0.8,
    "agent": "claude-code",
    "source_url": null
  }'
```

Confidence guide:
- `0.9` — clear decision made explicitly by the user
- `0.8` — strong pattern, validated in this session
- `0.6–0.7` — likely true, worth reviewing
- `0.5` — uncertain, worth flagging

If the server is not running, print the staged facts as a formatted list so the user can manually review or stage them later.

## Step 5: Report

After staging, show the user a summary table:

```
Staged N items to the curation queue:

  [ID]  [0.9]  Fact text preview...        → cto-knowledge
  [ID]  [0.8]  Another fact preview...     → anamnesis
  ...

Review with: anamnesis curation list
Confirm:     anamnesis curation confirm <id> --bolus <bolus_id>
Reject:      anamnesis curation reject <id>
```

If the API was unreachable, show the facts as a formatted list and remind the user to stage them manually once the server is running.
