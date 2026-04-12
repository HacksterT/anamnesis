# Anamnesis

A knowledge management framework for LLM agent systems. Library-first Python package that manages curated knowledge injection into any LLM via a single markdown file.

*Anamnesis* (ἀνάμνησις) — the act of recollection. In medicine, the patient history gathered before diagnosis. Here, the structured memory an agent carries into every conversation.

## What it does

Anamnesis organizes agent knowledge into **circles** — concentric layers of trust and refinement:

- **Circle 1 (Injection):** A single markdown file (`anamnesis.md`) injected into the LLM system prompt. The agent's working memory.
- **Circle 2 (Boluses):** A library of curated knowledge units — markdown files with YAML frontmatter. Each bolus can be toggled active/inactive to control what appears in the injection.

Future circles (curation, episode capture, behavioral mining) are planned but not yet implemented.

## Install

```bash
uv sync                  # base library
uv sync --extra dev      # + pytest, ruff
uv sync --extra api      # + FastAPI server (Phase 1, S05)
```

Requires Python 3.11+.

## Quick start

```python
from pathlib import Path
from anamnesis import KnowledgeConfig, KnowledgeFramework

config = KnowledgeConfig(
    circle1_path=Path("knowledge/anamnesis.md"),
    circle2_root=Path("knowledge/boluses"),
)

kf = KnowledgeFramework(config)

# Create a knowledge bolus
kf.create_bolus(
    "infrastructure",
    "Mac Mini M4 Pro running macOS. Ubuntu dev server. Tailscale mesh.",
    summary="Hardware and network topology.",
    tags=["technical"],
)

# Read it back
print(kf.read_bolus("infrastructure"))

# Toggle activation (controls Circle 1 inclusion)
kf.set_bolus_active("infrastructure", False)

# List active boluses
for bolus in kf.list_boluses():
    print(bolus["id"], bolus["summary"])
```

## Project structure

```
knowledge/
├── anamnesis.md              # Circle 1 — injection file
└── boluses/                  # Circle 2 — one .md per bolus

src/anamnesis/
├── config.py                 # KnowledgeConfig dataclass
├── framework.py              # KnowledgeFramework entry point
├── bolus/
│   ├── base.py               # BolusStore ABC (pluggable backend)
│   ├── store.py              # MarkdownBolusStore implementation
│   └── frontmatter.py        # YAML frontmatter parser
├── inject/                   # Circle 1 assembly (S04)
└── api/                      # FastAPI layer (S05)
```

## Status

Phase 1 in progress. See [tasks/](tasks/) for the full story map.

| Story | Description | Status |
|-------|-------------|--------|
| S01 | Project scaffolding & config | Done |
| S02 | Bolus system (Circle 2) | Done |
| S03 | anamnesis.md spec | Next |
| S04 | Injection assembly | Planned |
| S05 | API layer | Planned |

## License

Apache 2.0. See [LICENSE](LICENSE).
