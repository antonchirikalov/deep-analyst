# Deep Analyst

Multi-agent platform for GitHub Copilot with **two independent pipelines**: deep web research and architecture analysis. Both produce publication-quality documents with illustrations, peer review, and optional PDF/Confluence export.

Built on GitHub Copilot agent mode with 16 specialized agents, 2 Python state machines, and the PaperBanana illustration system.

![Platform Overview](docs/images/platform_overview.png)

---

## Two Pipelines

Deep Analyst provides two entry points — each launches a fully automated pipeline driven by a Python state machine. The orchestrator agent is a "dumb scheduler": it reads the next action from the script and executes it.

| | **Research Pipeline** | **Architecture Pipeline** |
|---|---|---|
| **Entry point** | `@research-orchestrator` | `@architecture-orchestrator` |
| **State machine** | `pipeline_runner.py` | `arch_pipeline_runner.py` |
| **Input** | Research question / topic | Code, docs, configs, Confluence, web |
| **Output** | Analytical document (15–100 pages) | Architecture proposal with options & trade-offs |
| **Folder prefix** | `generated_docs_*` | `generated_arch_*` |
| **Phases** | 0–9 (Decompose → Retrieve → Extract → Analyze → Plan → Write → Edit → Review → Illustrate → Deliver) | 0–9 (Decompose → Source Analysis → Assess → Propose → Plan → Write → Edit → Review → Illustrate → Deliver) |

### Shared components

Both pipelines share these agents and infrastructure:
- **Planner** — builds Table of Contents with page budgets
- **Writer** (Opus) — writes one section at a time from source material
- **Editor** (Opus) — merges sections, deduplicates, adds transitions
- **Critic** — structured review with APPROVED / REVISE verdict
- **Illustrator** — PaperBanana PNG generation via `gpt-image-1.5`
- **PDF Exporter** — Markdown → PDF conversion
- **Confluence Publisher** — publishes to Confluence with images via REST API

---

## Pipeline 1: Research

The **Research Pipeline** takes a topic, searches the web, extracts full content from sources, and produces a structured analytical document.

![Research Pipeline](docs/images/research_pipeline.png)

### How to use

```
@research-orchestrator
Compare GitHub Copilot Agents, Claude Code, and OpenAI Codex CLI.
Type: comparative analysis, Language: Russian, Size: detailed
```

The Orchestrator parses the query, applies defaults for missing parameters, and launches the pipeline. **It never asks for clarification.**

### Phases

| Phase | Agent | Action | Output |
|-------|-------|--------|--------|
| 0 | Orchestrator | Parse query → `params.md` with subtopics | `research/_plan/params.md` |
| 1 | Orchestrator | Web search (Tavily / fetch_webpage / GitHub / HuggingFace) | `research/{subtopic}/_links.md` |
| 2 | Orchestrator | Extract full content from each URL | `research/{subtopic}/extract_*.md` |
| 3 | Analyst ×N | Analyze extracts per subtopic → section proposals | `research/{subtopic}/_structure.md` |
| 4 | Planner | Build unified Table of Contents | `research/_plan/toc.md` |
| 5 | Writer ×M | Write sections in parallel (one per ToC entry) | `draft/_sections/NN_*.md` |
| 6 | Editor | Merge all sections into cohesive document | `draft/v1.md` |
| 7 | Critic | Review → APPROVED or REVISE (max 2 loops) | `draft/_review.md` |
| 8 | Illustrator | Generate PNGs via PaperBanana, embed in draft | `illustrations/*.png` |
| 9 | — | Delivery: stats, paths, next steps | — |

### Parameters

All parameters are **optional** — sensible defaults are applied.

| Parameter | Values | Default |
|-----------|--------|---------|
| **Size** | `brief` (15–20p), `standard` (30–40p), `detailed` (60–100p) | `standard` |
| **Language** | Any | Auto-detected from query |
| **Document type** | `comparison`, `overview`, `sota`, `report` | Auto-detected |
| **Illustrations** | `on` / `off` | `on` |

### Research agents

| Agent | Model | Role |
|-------|-------|------|
| **Research Orchestrator** | Sonnet | Entry point, dumb scheduler |
| **Retriever** | Haiku | URL discovery per subtopic |
| **Extractor** | Sonnet | Full content extraction from URLs |
| **Analyst** | Sonnet | Per-subtopic structure analysis |

---

## Pipeline 2: Architecture

The **Architecture Pipeline** analyzes existing code, documentation, and infrastructure to produce architecture proposals with trade-offs, risk assessment, and migration paths.

![Architecture Pipeline](docs/images/architecture_pipeline.png)

### How to use

```
@architecture-orchestrator
Redesign the LLM Orchestrator service. Improve modularity and testability.
Target: /path/to/repo, Size: standard, Language: Russian
```

The Orchestrator parses the request, identifies sources (code, docs, configs, web, Confluence), and launches the pipeline.

### Sources

The pipeline supports 5 source types in `params.md`:

```markdown
## Sources
1. Main codebase — path: /repo/app — type: code
2. Infrastructure — path: /repo/docker-compose.yml — type: config
3. Architecture docs — path: /repo/docs — type: docs
4. Industry patterns — query: "microservices patterns" — type: web
5. Team wiki — confluence: space=ARCH, title=Current Design — type: confluence
```

| Type | Handler | What it does |
|------|---------|-------------|
| `code` | Source Analyzer (sub-agent) | Reads files, extracts module structure, APIs, patterns |
| `docs` | Source Analyzer (sub-agent) | Extracts ADRs, requirements, constraints |
| `config` | Source Analyzer (sub-agent) | Maps infrastructure topology, env vars, dependencies |
| `web` | Orchestrator (direct) | Fetches web pages, extracts content |
| `confluence` | Orchestrator (direct) | Reads Confluence pages via MCP/REST |

### Phases

| Phase | Agent | Action | Output |
|-------|-------|--------|--------|
| 0 | Orchestrator | Parse request → `params.md` with `## Sources` | `research/_plan/params.md` |
| 1a | Orchestrator | Fetch web / Confluence sources directly | `research/{area}/extract_*.md` |
| 1b | Source Analyzer ×N | Analyze code / docs / config in parallel | `research/{area}/extract_*.md` |
| 2 | Arch Assessor ×N | Per-area assessment: patterns, tech debt, dependencies | `research/{area}/_assessment.md` |
| 3 | Solution Architect | Design 2–3 architecture options with trade-offs | `research/_plan/_proposals.md` |
| 4 | Planner | Build ToC for proposal document | `research/_plan/toc.md` |
| 5 | Writer ×M | Write sections in parallel | `draft/_sections/NN_*.md` |
| 6 | Editor | Merge into cohesive document | `draft/v1.md` |
| 7 | Critic | Review with architecture-specific criteria | `draft/_review.md` |
| 8 | Illustrator | Generate architecture diagrams | `illustrations/*.png` |
| 9 | — | Delivery + optional Confluence publish / PDF export | — |

### Architecture-specific agents

| Agent | Model | Role |
|-------|-------|------|
| **Architecture Orchestrator** | Sonnet | Entry point, handles web/Confluence I/O |
| **Source Analyzer** | Sonnet | Scans code, docs, configs → structured extracts |
| **Arch Assessor** | Sonnet | Per-area architecture assessment (patterns, debt, risks) |
| **Solution Architect** | Opus | Synthesizes assessments → 2–3 proposals with recommendation |

---

## Core Design Principles

**Files = Protocol.** Agents communicate only through files on disk. No in-memory state sharing.

**Folders = Routing.** Each subtopic (research) or source area (architecture) gets its own folder under `research/`.

**Orchestrator = Dumb Scheduler.** The Python state machine (`pipeline_runner.py` / `arch_pipeline_runner.py`) decides the next phase. The orchestrator agent just executes.

**Sub-agents return text.** Due to VS Code Copilot limitations, sub-agents cannot reliably write files or use MCP tools. The orchestrator handles all file I/O.

**Deterministic phases.** Each phase has validation gates. The state machine checks word counts, file existence, and structural integrity before advancing.

---

## PaperBanana Illustration System

Both pipelines use **PaperBanana** to generate publication-quality PNG diagrams — no Mermaid, no ASCII art, no screenshots.

| Mode | When to use | Command |
|------|-------------|---------|
| `--direct` | Architecture diagrams, flowcharts, comparisons | `paperbanana_generate.py "prompt" "output.png" --direct` |
| `--context` | Data visualizations, methodology figures | `paperbanana_generate.py "desc" "output.png" --context "text"` |

**Visual style:** NeurIPS 2025 academic aesthetic — flat vector, 2D, white background, pastel palette, clean typography.

**Placeholder format** (written by Writer, processed by Illustrator):
```markdown
<!-- ILLUSTRATION: type="architecture", section="§2", description="..." -->
```

---

## Publishing

### PDF Export
```
@pdf-exporter
Export generated_docs_20260310_120000/draft/v1.md to PDF
```

### Confluence Publish
```
@confluence-publisher
Publish generated_arch_20260310_150000/draft/v1.md
to space=ARCH, title=LLM Orchestrator Proposal
```
Confluence Publisher uses **REST API** for image uploads (MCP cannot upload images). Requires `CONFLUENCE_URL`, `CONFLUENCE_USER`, `CONFLUENCE_TOKEN` env vars.

---

## Project Structure

```
.github/
  agents/                       # 16 agent definitions
    research-orchestrator.agent.md   # Pipeline 1 entry point
    architecture-orchestrator.agent.md  # Pipeline 2 entry point
    retriever.agent.md           # URL discovery
    extractor.agent.md           # Content extraction
    analyst.agent.md             # Structure analysis
    source-analyzer.agent.md     # Code/docs/config scanning
    arch-assessor.agent.md       # Architecture assessment
    solution-architect.agent.md  # Proposal generation
    planner.agent.md             # ToC builder
    writer.agent.md              # Section writer
    editor.agent.md              # Document merger
    critic.agent.md              # Peer review
    illustrator.agent.md         # PNG generation
    pdf-exporter.agent.md        # PDF conversion
    confluence-publisher.agent.md # Confluence publishing
    deterministic-orchestrator.agent.md  # Legacy orchestrator
  instructions/                  # Per-agent instruction files
  scripts/
    pipeline_runner.py           # Research pipeline state machine
    arch_pipeline_runner.py      # Architecture pipeline state machine
    validate_agents.py           # Agent file validator
  skills/
    image-generator/             # PaperBanana wrapper scripts
    workflow-logger/             # Phase logging utilities
generated_docs_*/                # Research pipeline output folders
generated_arch_*/                # Architecture pipeline output folders
```

---

## Quick Start

### Research document
```
@research-orchestrator
What is WebAssembly and how does it work? Size: standard
```

### Architecture proposal
```
@architecture-orchestrator
Redesign the authentication module. Improve security and testability.
Target: /path/to/project, Size: standard
```

### Continue an interrupted pipeline
```
@research-orchestrator continue generated_docs_20260310_120000
@architecture-orchestrator continue generated_arch_20260310_150000
```

Both pipelines checkpoint between phases — you can close the conversation and resume later in a new one..

---

## Output Structure

Each pipeline run creates a timestamped folder:

```
generated_docs_YYYYMMDD_HHMMSS/
├── workflow_log.md              # Full pipeline execution log with timestamps
├── research/                    # Raw Scout findings (one file per subtopic)
│   ├── github_copilot_agents.md
│   ├── claude_code.md
│   └── openai_codex_cli.md
├── draft/                       # Document versions
│   ├── v1.md                    # Initial Analyst draft
│   └── v2.md                    # Post-Critic revision (if needed)
├── illustrations/               # PaperBanana PNG diagrams
│   ├── _manifest.md             # Diagram metadata and prompts used
│   ├── diagram_1.png            # Final selected illustration
│   ├── diagram_1_a.png          # Candidate A (kept for audit)
│   └── ...
└── FINAL_REPORT.md              # Approved document (copy of best draft version)
```

---

## Setup

### Prerequisites

- **VS Code** 1.100+ with **GitHub Copilot** extension (agent mode)
- **Python 3.10+**
- **OpenAI API key** (for PaperBanana illustrations via `gpt-image-1.5`)

### 1. Clone the repo

```bash
git clone https://github.com/antonchirikalov/deep-analyst.git
```

### 2. Add to your project as a secondary workspace folder

Deep Analyst agents live inside `.github/agents/`. VS Code Copilot discovers agents from **all workspace folders**. Two ways to connect:

**Option A — Multi-root workspace (recommended):**

Open your project, then `File → Add Folder to Workspace…` → select the cloned `deep-analyst` folder. Save the workspace (`File → Save Workspace As…`). Now all 16 agents are available in Copilot Chat alongside your project files.

**Option B — Symlink `.github` into your project:**

```bash
# From your project root:
ln -s /path/to/deep-analyst/.github/agents .github/agents
ln -s /path/to/deep-analyst/.github/instructions .github/instructions
ln -s /path/to/deep-analyst/.github/scripts .github/scripts
ln -s /path/to/deep-analyst/.github/skills .github/skills
```

> **Note:** Option A is cleaner — no symlinks to maintain, easy to update with `git pull`.

### 3. Configure environment

```bash
cd deep-analyst
cp .env.example .env
# Edit .env — add your OpenAI API key:
# OPENAI_API_KEY=sk-...
```

### 4. Configure MCP servers

Add MCP servers to your VS Code settings (`settings.json`) or `.vscode/mcp.json`:

```jsonc
// .vscode/mcp.json (in your workspace)
{
  "servers": {
    "tavily": {
      "type": "http",
      "url": "https://mcp.tavily.com/mcp",
      "headers": { "Authorization": "Bearer YOUR_TAVILY_API_KEY" }
    },
    "github": {
      "command": "docker",
      "args": ["run", "-i", "--rm",
        "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
        "ghcr.io/github/github-mcp-server"],
      "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_..." }
    }
  }
}
```

| MCP Server | Purpose | Required? |
|------------|---------|-----------|
| **Tavily** | Web search + content extraction | Recommended (fallback: `fetch_webpage`) |
| **GitHub** | Repository search, code exploration | Optional |
| **HuggingFace** | Paper/model search | Optional |
| **Atlassian** | Confluence read/write | Only for Confluence publishing |

### 5. Verify agents are loaded

Open Copilot Chat (`Cmd+Shift+I`), type `@` and check that `research-orchestrator` and `architecture-orchestrator` appear in the agent list. If they don't — make sure the `deep-analyst` folder is in your workspace.

## License

MIT
