---
title: "Anamnesis -- Behavioral Mining: Curation and the 80/20 Principle"
source: "https://youtu.be/ro5jpbi5uYc"
date_processed: "2026-04-09"
content_type: "analysis"
related: "anamnesis-framework.md, Section 9.3"
---

# Anamnesis -- Behavioral Mining: Curation and the 80/20 Principle

## Origin

Nate's video covers Anthropic's leaked "Conway" project -- an always-on persistent agent discovered in the Claude Code source leak. The technical details (extension format, proprietary CNW.zip layer on MCP, platform lock-in strategy) are interesting but secondary. The load-bearing insight is about behavioral context -- the accumulated model of how you work -- and the lock-in risk it creates.

Nate's core argument: the deepest form of platform lock-in is not data. It is behavioral context. Not your files, but the patterns the agent learned by watching you use them. Not your Slack messages, but the understanding of which messages you respond to in five minutes and which you ignore for three days. When you switch agents after six months of accumulated behavioral learning, you lose the compounding.

The concern is legitimate. The proposed solution (collect everything, learn everything) is wrong.

## Classification: Not a Fourth Knowledge Type

Initial analysis proposed behavioral knowledge as a fourth type alongside declarative, procedural, and episodic, warranting its own Section 9.4. On further examination, behavioral knowledge is a **compilation output from episodic data**, not a separate type.

Every behavioral pattern, once extracted and confirmed, becomes a declarative fact:

- "HacksterT responds to infrastructure alerts within 15 minutes but defers marketing questions by 4 hours" is a declarative fact about communication priorities, extracted from hundreds of episodic records.
- "When HacksterT edits agent-generated prose, 80% of edits remove qualifiers" is a declarative fact about editing preferences, derived from episodic records of editing sessions.
- "HacksterT consistently chooses the architecturally cleaner option over the faster option" is already in CLAUDE.md as a stated principle. The behavioral observation confirms the declarative statement with different provenance.

What is distinct is the **compilation method**, not the knowledge type. Declarative extraction reads one episode and pulls out facts. Behavioral extraction reads fifty episodes and detects statistical patterns. The output of both is declarative knowledge. The input of both is episodic knowledge. The difference is the pipeline, not the product.

**Integration path:** Extend the compilation pipeline (framework Section 9.3.3) with a behavioral analysis mode rather than creating a separate section. Behavioral patterns are deposited in Circle 3 as candidate declarative facts with `provenance: system-observed-behavioral` and a confidence score based on observation count. They follow the same reconciliation path as any other Circle 3 content and land in Circle 2 as entries in a behavioral profile bolus.

The four-circle model, reconciliation process, and permissiveness slider apply without modification.

## The Real Problem: Behavioral Mining

The more practical question is not "is behavioral knowledge a separate type?" but "how do you observe behavior in the first place?"

Agent-detected behavioral knowledge -- what the agent learns by watching you interact with it -- is a narrow slice of actual behavior. Most behavior happens outside the agent. How you use your operating system. Which apps you open first in the morning. How you organize files. What browser tabs stay open for days. How often you switch between projects. What you read vs. what you bookmark vs. what you act on. What version of the Bible you study from and how frequently.

This behavioral data lives in dozens of systems, none of which feed the agent by default. Conway's approach (and the approach most AI companies are pursuing) is to become the always-on layer that observes everything. That's the lock-in play: the agent watches your screen, your files, your communications, and builds a behavioral model that lives inside their infrastructure.

The alternative: **deterministic micro-pipelines that mine specific behavioral signals from specific systems and feed them into the knowledge framework's existing architecture.**

### Micro-Pipeline Architecture

A micro-pipeline is a small, focused, deterministic script that:

1. Observes one specific behavioral signal from one specific system
2. Extracts a structured observation
3. Deposits it in Circle 4 (raw episodic capture) or Circle 3 (if the extraction is already pattern-level)

Micro-pipelines are not AI. They are scripts -- cron jobs, launchd agents, system hooks, log parsers. They run on your infrastructure, observe your systems, and feed the knowledge framework. The LLM is involved only at the compilation stage (Circle 4 → Circle 3 pattern detection), not at the observation stage.

```
┌─────────────────────────────────────────────────────────────┐
│                  BEHAVIORAL MINING SERVICE                    │
│                                                              │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│   │ OS Usage      │  │ App Patterns  │  │ Bible Study  │     │
│   │ micro-pipe    │  │ micro-pipe    │  │ micro-pipe   │     │
│   │               │  │               │  │              │     │
│   │ - keystrokes  │  │ - app switch  │  │ - version    │     │
│   │ - shortcuts   │  │   frequency   │  │   used       │     │
│   │ - bad habits  │  │ - time-in-app │  │ - frequency  │     │
│   │ - efficiency  │  │ - tab count   │  │ - duration   │     │
│   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│          │                 │                  │              │
│          └────────────────┬┘──────────────────┘              │
│                           │                                  │
│                           ▼                                  │
│              ┌────────────────────────┐                      │
│              │  Circle 4              │                      │
│              │  (raw behavioral       │                      │
│              │   observations)        │                      │
│              └────────────┬───────────┘                      │
│                           │                                  │
│              (compilation pipeline --                        │
│               behavioral analysis mode)                      │
│                           │                                  │
│                           ▼                                  │
│              ┌────────────────────────┐                      │
│              │  Circle 3              │                      │
│              │  (candidate behavioral │                      │
│              │   patterns, awaiting   │                      │
│              │   reconciliation)      │                      │
│              └────────────────────────┘                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
         │                                    │
         ▼                                    ▼
  Circle 2 (behavioral               Circle 1 (behavioral
  profile bolus, confirmed)           summary in injection)
```

Each micro-pipeline is:
- **Scoped to one system.** The OS usage pipeline doesn't touch Bible study data. The app pattern pipeline doesn't touch communication logs. Isolation by design.
- **Deterministic.** No LLM calls. A script that reads a log file, counts events, and writes a structured observation. Cheap, fast, reliable.
- **Configurable by the user.** The user decides which micro-pipelines run. Not all behaviors are worth observing. The user enables the OS usage pipeline because they want tips on Mac efficiency. They enable the Bible study pipeline because they want Selah to understand their study habits. They don't enable a communication pattern pipeline because they don't want the agent analyzing their email latency.
- **Agent-specific routing.** The OS usage pipeline feeds Atlas (personal infrastructure agent). The Bible study pipeline feeds Selah (theological agent). Different agents receive different behavioral signals. The routing is configured, not inferred.

### Examples

**Mac Mini usage micro-pipeline (feeds Atlas):**
- Monitors keyboard shortcuts used vs. available (are you doing things the hard way?)
- Tracks app-switching frequency (are you context-switching excessively?)
- Logs common terminal commands (are there aliases you should be using?)
- Deposits structured observations in Circle 4: "2026-04-09: User manually navigated to Applications folder 7 times instead of using Spotlight. User typed full file paths instead of using tab completion 12 times."
- Behavioral compilation detects the pattern, deposits in Circle 3: "User appears unfamiliar with macOS keyboard navigation. Suggest Spotlight (Cmd+Space) and tab completion."
- After reconciliation to Circle 2, the agent can offer real-time tips: "You've been opening Finder to get to Applications -- try Cmd+Space and type the app name."

**Bible study micro-pipeline (feeds Selah):**
- Tracks which Bible version is opened (ESV, NASB, KJV)
- Logs study session frequency and duration
- Records which books/chapters are studied most
- Deposits in Circle 4: "2026-04-09: 45-minute session, Romans 8, ESV. 2026-04-07: 30-minute session, Psalms 119, NASB."
- Behavioral compilation: "Primary study version is ESV (used 70% of sessions). Current focus area is Pauline epistles (Romans, Ephesians, Galatians in last 30 days)."
- After reconciliation, Selah knows which translation to reference by default and can connect new study material to the current focus area.

## The 80/20 Principle: Why Comprehensive Collection Is Wrong

Nate's video implies (and Conway's design assumes) that comprehensive behavioral observation is the goal. Observe everything, learn everything, build the most complete model possible. This is wrong for three reasons that compound.

**Reason 1: Context window economics.** Even if you collect every behavioral signal, the agent cannot use it all. The injection file has a fixed token budget. The behavioral profile bolus in Circle 2 has a practical size limit. Collecting 10,000 behavioral observations to produce a 500-word behavioral profile means 95% of the collection was wasted. The compilation pipeline does the reduction, but why collect what you know you'll discard?

**Reason 2: Signal-to-noise ratio.** Most behavior is not informative. The fact that you opened Chrome 47 times today tells the agent nothing useful. The fact that you opened Chrome, went to three specific documentation sites, and spent 20 minutes reading Gemini API docs before switching to your voice agent code -- that tells the agent something. But you only get the signal by curating which behaviors to observe. Comprehensive collection produces a haystack. Curated collection produces the needles.

**Reason 3: Processing cost.** Every behavioral observation that enters Circle 4 eventually needs to be processed by the compilation pipeline. If the pipeline uses an LLM (which it does for pattern detection), that processing has a cost. Anthropic, OpenAI, Google -- they are happy to process all of your behavioral data because you're paying for it. The smarter approach is to decide upfront which 20% of your behaviors give 80% of the useful signal, mine those specifically, and skip the rest.

This is the clinical standard applied to behavioral observation. A physician doesn't order every possible lab test on every patient. They order the tests that are decision-relevant given the clinical picture. The observation strategy should match the decision context. What behavioral signals would actually change how the agent behaves? Those are worth mining. Everything else is cost without utility.

**The front-end curation principle:** The user decides which micro-pipelines to enable. The user decides which behavioral domains are worth observing. The user reviews extracted patterns through reconciliation. At no point does the system decide on its own that a behavior is worth tracking. This is the same curation principle that governs declarative knowledge (Section 9.1) applied to behavioral observation: the agent reads, the human writes. The micro-pipeline observes, the human decides what's worth keeping.

This is why a curated behavioral mining approach is better than Conway's comprehensive surveillance. Not because comprehensive data wouldn't be useful in theory, but because:
- The token budget makes comprehensive injection impossible anyway
- The processing cost makes comprehensive compilation expensive
- The signal-to-noise ratio makes comprehensive collection counterproductive
- The curation step is where the real value is created, and front-loading it saves everything downstream

## Portability

Behavioral knowledge compiled through this framework is portable by design:

- **Self-hosted.** Micro-pipelines run on your machines. Circle 4 observations, Circle 3 candidates, and Circle 2 confirmed profiles live in your storage.
- **Exportable.** The behavioral profile bolus is structured markdown. Human-readable, git-friendly, transferable.
- **Provider-agnostic.** The behavioral summary in Circle 1 is plain text injected into any LLM's system prompt. Switch from Claude to Gemini to a local model and the behavioral profile goes with you.

This is not a special behavioral feature. It is a consequence of the framework's design. All Circle 2 boluses are portable. The behavioral profile is one bolus among many.

The lock-in risk Nate identifies is real, but it applies to Conway's architecture (behavioral model embedded in provider infrastructure) not to this one (behavioral model as a self-hosted, exportable bolus).

## What To Build

1. **Extend the compilation pipeline (framework Section 9.3.3)** with a behavioral analysis mode. Cross-episode pattern detection with confidence scores, observation counts, recency weighting, and drift detection.

2. **Add stated-vs-observed contradiction detection** to the reconciliation process. When the behavioral compilation proposes a pattern that contradicts a stated preference in an existing declarative bolus, surface both during reconciliation.

3. **Design the behavioral profile bolus template.** Structured sections: communication patterns, decision patterns, work patterns, quality standards. Entries include confidence score and observation count.

4. **Build the micro-pipeline framework.** A lightweight, deterministic observation service. Configurable per agent, per system. Deposits structured observations in Circle 4. Runs on cron/launchd. No LLM calls at the observation layer.

5. **Implement agent-specific routing.** Each micro-pipeline is tagged with the agent it feeds. OS usage → Atlas. Bible study → Selah. Business call patterns → the-agency voice agents. The mining service knows where to deposit its observations.

6. **Design the micro-pipeline configuration interface.** A dashboard or config file where the user enables/disables specific behavioral observers. The 80/20 decision is made here -- which behaviors are worth tracking for which agents.

## Integration with Knowledge Framework

### The Five-Circle Model

Behavioral knowledge does not require a Section 9.4 (it is not a separate knowledge type). It does require a **Circle 5** -- a separate source layer distinct from Circle 4's episodic capture.

The distinction is not about knowledge type but about knowledge source:

- **Circle 4 (Episodic Capture)** is a byproduct of agent interaction. Transcripts, call logs, session records. These exist because the conversation happened. The source is the agent's own interactions.
- **Circle 5 (Behavioral Mining)** is the product of deliberate observation pipelines deployed across systems outside the agent. OS usage patterns, app behavior, study habits, system logs. These exist because the user decided that specific behaviors were worth watching. The source is the user's broader digital life, not the agent interaction.

Both are source layers. Both feed Circle 3. But they come from fundamentally different places, through fundamentally different mechanisms, and under fundamentally different governance.

```
              ┌───────────────┐
              │   CIRCLE 1    │   Always injected. Single file.
              │   Injection   │   Constant-sized.
              │   Point       │
              └───────┬───────┘
                      │
         ┌────────────┴───────────┐
         │       CIRCLE 2         │   Confirmed knowledge boluses.
         │  ┌────┐ ┌────┐ ┌────┐ │   Technology determined by
         │  │ B1 │ │ B2 │ │ B3 │ │   triage questions (Section 2).
         │  └────┘ └────┘ └────┘ │
         └────────────┬──────────┘
                      │
         ┌────────────┴──────────┐
         │       CIRCLE 3         │   Agent's curation layer.
         │   All sources          │   Front-end curation gate.
         │   converge here.       │   The moat.
         └──────┬─────────┬──────┘
                │         │
       ┌────────┴──┐  ┌───┴───────────┐
       │  CIRCLE 4  │  │   CIRCLE 5    │
       │  Episodic  │  │   Behavioral  │
       │  Capture   │  │   Mining      │
       │            │  │               │
       │ Byproduct  │  │ Deliberate    │
       │ of agent   │  │ observation   │
       │ interaction│  │ pipelines     │
       └────────────┘  └──────────────┘
```

### Why Circle 5 Is Separate from Circle 4

Circle 4 accumulates passively. Every agent session produces a transcript whether or not anyone asked for it. Circle 5 accumulates deliberately. Each micro-pipeline is a conscious decision to observe a specific behavior from a specific system. The user enables it, configures it, and can disable it at any time.

This distinction matters for governance:
- Circle 4 governance: automated capture, compilation pipeline reads and extracts, retention policy manages lifecycle.
- Circle 5 governance: **user decides which pipelines exist**. This is the front-end curation principle in its purest form. The 80/20 decision -- which 20% of behaviors yield 80% of the useful signal -- is made at Circle 5 deployment time, not at compilation time. By the time an observation enters Circle 5, the user has already decided it's worth watching. The filtering happened before collection, not after.

### Technology Is Not Prescribed Per Circle

The technology underlying each circle is a deployment decision, not an architectural constant. The triage questions (Section 2) determine the right storage and retrieval mechanism for each circle in each use case:

| Circle | Technology Driver | Small Scale | Large Scale |
|--------|------------------|-------------|-------------|
| 1 | Always text. Token-optimized. | Markdown file (CLAUDE.md) | Token-optimized format (TOON or equivalent) |
| 2 | Triage Q2 (volume) and Q7 (query pattern) | Markdown files, deterministic lookup | Embedded vectors, hybrid FTS + semantic search |
| 3 | Reconciliation queue requirements | JSON file or SQLite table | Database with priority indexing |
| 4 | Append-only, temporal access | Directory of transcripts | Time-series or indexed document store |
| 5 | Per-pipeline observation format | JSON files per pipeline | Time-series DB, structured logs |

The circle model defines the conceptual architecture: what goes where, what trust level it carries, how it moves between layers, and who governs the movement. The storage technology is a separate decision made per deployment through the framework's triage process. Prescribing JSON for Circle 5 or markdown for Circle 2 as universal choices would violate the framework's own principle that architecture should match the use case.

### Component Mapping

| Framework Component | Behavioral Integration |
|---------------------|----------------------|
| Circle 5 (new) | Micro-pipeline observations. Separate source layer from episodic capture. User-configured, deliberately deployed. |
| Circle 4 | Episodic capture (unchanged). Transcripts, call logs, session records from agent interactions. |
| Circle 3 | All sources converge here. Behavioral pattern candidates from Circle 5 compilation sit alongside declarative fact candidates from Circle 4 compilation. Front-end curation gate. |
| Circle 2 | Behavioral profile bolus (confirmed patterns, structured by domain). One bolus among many. Technology per triage questions. |
| Circle 1 | Behavioral summary line + pointer to profile bolus. Part of the single injection file. |
| Compilation pipeline (9.3.3) | Extended with behavioral analysis mode: cross-episode pattern detection from Circle 5, confidence scoring, drift detection. Separate from Circle 4 episodic compilation but routes to the same Circle 3. |
| Reconciliation (9.1.7) | Extended with stated-vs-observed contradiction detection. Behavioral candidates reconciled alongside all other Circle 3 content. |
| Permissiveness slider (9.1.7) | Applies to behavioral patterns same as any other Circle 3 content. |
| Extraction prompts (Section 6) | Behavioral extraction prompt is a separate configurable artifact, domain-specific per micro-pipeline. |
| Portability | Behavioral profile is a Circle 2 bolus -- self-hosted, exportable, provider-agnostic by design. |

### Front-End Curation as the Moat

The framework's competitive advantage is not in collection sophistication or retrieval infrastructure. It is in curation discipline. The front-end curation principle operates at every level:

- **Circle 5 deployment:** The user decides which micro-pipelines to run. This is the 80/20 filter. Which behaviors are worth watching? The decision is made before a single observation is collected.
- **Circle 3 reconciliation:** The user reviews candidate patterns extracted from Circles 4 and 5. Confirm, reject, defer. The agent proposes; the human decides.
- **Circle 2 bolus management:** The user decides which boluses an agent has access to. Plug in, plug out.
- **Circle 1 composition:** The user governs what earns a place in the injection file. The constant-sized token budget forces selectivity.

At every layer, the human is curating. No layer auto-populates without governance. No observation enters the system without the user having decided (at Circle 5 deployment time or Circle 3 reconciliation time) that it's worth keeping.

This is why comprehensive collection is the wrong approach. It defers curation to the compilation pipeline, which defers it to the reconciliation queue, which overwhelms the human, which leads to reconciliation fatigue (Section 10.1), which leads to either auto-confirmation (noise enters Circle 2) or abandonment (the system stops learning). Front-end curation -- deciding what to observe before observing it -- breaks this chain at the source.

No matter how good the technology, you can only handle so much information. The system that curates wisely beats the system that collects comprehensively. Every time.
