# Deep Analyst

Multi-agent research pipeline for GitHub Copilot. Automates deep research, synthesis, illustration generation, and quality review — producing publication-ready analytical documents.

## Architecture

```
User Query → Orchestrator → Scout (parallel) → Analyst → Illustrator → Critic → Final Report
```

**6 agents** working in a coordinated pipeline:

| Agent | Model | Role |
|-------|-------|------|
| **Research Orchestrator** | Haiku 4.5 | Pipeline coordinator. Decomposes topics, launches agents, manages iterations |
| **Scout** | Haiku 4.5 | Information gatherer. Parallel web research via Tavily, Context7, GitHub, HuggingFace |
| **Analyst** | Opus 4.6 | Synthesis specialist. Builds structured documents with tables, placeholders, conclusions |
| **Illustrator** | Sonnet 4.6 | PaperBanana-style PNG diagram generator using OpenAI gpt-image-1 |
| **Research Critic** | Sonnet 4.6 | Quality reviewer. Returns APPROVED / REVISE / REJECTED verdicts |
| **PDF Exporter** | Haiku 4.5 | Converts final document to PDF |

## Pipeline Phases

```
Phase 0: Parse parameters (doc type, size, language, search depth)
Phase 1: Scout — parallel research across 3-6 subtopics
Phase 2: Analyst — synthesis into structured draft with illustration placeholders
Phase 3: Illustrator — PaperBanana PNG generation, replaces placeholders
Phase 4: Critic — review, iterate if needed (max 3 rounds)
Phase 5: Delivery — final document
```

## Illustration System

Uses the **PaperBanana method** — zone-based Golden Schema prompts producing NeurIPS-quality academic illustrations via OpenAI `gpt-image-1`. No Mermaid, no code-based diagrams — only publication-quality PNGs.

The Analyst inserts `<!-- ILLUSTRATION -->` placeholders → Illustrator parses them → generates 2-3 candidates per diagram → selects best → replaces placeholders with image references.

## Project Structure

```
.github/
├── agents/                          # Agent definitions (6 agents)
│   ├── research-orchestrator.agent.md
│   ├── scout.agent.md
│   ├── analyst.agent.md
│   ├── illustrator.agent.md
│   ├── research-critic.agent.md
│   └── pdf-exporter.agent.md
├── instructions/                    # Detailed instructions per agent
│   ├── analyst/                     # Document templates, quality, synthesis, illustration guidelines
│   ├── illustrator/                 # Generation pipeline, style guidelines (PaperBanana)
│   ├── research-critic/             # Review checklist, verdict rules
│   ├── research-orchestrator/       # Workflow phases, topic decomposition
│   ├── scout/                       # Search strategy, tiered search, source quality
│   └── shared/                      # Artifact management, documentation standards
└── skills/                          # Reusable skills
    ├── image-generator/             # gpt-image-1 wrapper (generate_image.py)
    └── workflow-logger/             # Structured markdown logging (workflow-logger.py)
.env.example                         # Environment template
.gitignore
```

## Setup

1. Clone the repo
2. Copy `.env.example` → `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=sk-...
   ```
3. Open in VS Code with GitHub Copilot extension
4. Ensure MCP servers are configured: Tavily, Context7, HuggingFace, GitHub

## Usage

In Copilot Chat, invoke the orchestrator:

```
@research-orchestrator

Compare React, Vue, and Svelte frameworks.
Type: comparative analysis
Language: English
```

Parameters (all optional — defaults applied automatically):
- **Size:** `brief` (15-20 pages), `standard` (30-40 pages), `detailed` (60-100 pages)
- **Search depth:** `quick`, `normal`, `deep` (auto-derived from size if not set)
- **Illustrations:** always ON (disable with `no illustrations`)
- **Language:** detected from query

## Output

Each run creates a timestamped folder:

```
generated_docs_YYYYMMDD_HHMMSS/
├── workflow_log.md          # Pipeline execution log
├── research/                # Raw Scout findings
├── draft/                   # Document versions (v1.md, v2.md...)
├── illustrations/           # PaperBanana PNGs + manifest
└── FINAL_REPORT.md          # Approved document
```

## Requirements

- VS Code with GitHub Copilot (agent mode)
- Python 3.10+ (for image generation and logging scripts)
- OpenAI API key (for gpt-image-1 illustrations)
- MCP servers: Tavily, Context7 (optional: HuggingFace, GitHub)

## License

MIT
