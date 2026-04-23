# Deep Analyst

Multi-agent platform for GitHub Copilot with **two independent pipelines**: deep web research and architecture analysis. Both produce publication-quality documents with illustrations, peer review, and optional PDF/Confluence export.

Built on GitHub Copilot agent mode with **15 specialized agents**, **2 Python state machines**, and the **PaperBanana** illustration system (`gpt-image-1.5`).

![Platform Overview](docs/images/platform_overview.png)

---

## Two Pipelines

Each pipeline is driven by a Python state machine. The orchestrator agent is a "dumb scheduler": it reads the next action from the script and executes it.

| | **Research Pipeline** | **Architecture Pipeline** |
|---|---|---|
| **Entry point** | `@research-orchestrator` | `@architecture-orchestrator` |
| **State machine** | `research_pipeline_runner.py` | `arch_pipeline_runner.py` |
| **Input** | Research question / topic | Code, docs, configs, Confluence, web |
| **Output** | Analytical document (15–100 pages) | Architecture proposal with options & trade-offs |
| **Folder prefix** | `generated_docs_*` | `generated_arch_*` |
| **Phases** | 0–8 | 0–9 |

### Shared components

Both pipelines share these agents and infrastructure:
- **Planner** (Opus 4.6) — builds Table of Contents with page budgets and source assignments
- **Writer** (Opus 4.6) — writes one section at a time from source material
- **Editor** (Opus 4.6) — merges sections, deduplicates, adds transitions and executive summary
- **Critic** (Sonnet 4.6) — structured review with APPROVED / REVISE verdict (max 2 revision loops)
- **Illustrator** (Sonnet 4.6) — PaperBanana PNG generation (`gpt-5.2` VLM + `gpt-image-1.5` image gen)
- **PDF Exporter** (Haiku 4.5) — Markdown → PDF via WeasyPrint with publication-quality CSS
- **Confluence Publisher** (Haiku 4.5) — publishes to Confluence with images via REST API

### Standalone agents

- **Requirements Analyst** (Opus 4.6) — reads input documents (briefs, transcripts, designs, Q&A) and produces structured `_requirements.md` with traceability, conflict detection, and gap analysis. Use as a pre-pipeline step before Architecture Orchestrator.

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
| 1 | Researcher ×N | Search + extract per subtopic (parallel, write files directly) | `research/{subtopic}/_links.md` + `extract_*.md` |
| 2 | Analyst ×N | Analyze extracts per subtopic → section proposals (parallel) | `research/{subtopic}/_structure.md` |
| 3 | Planner | Build unified Table of Contents with page budgets | `research/_plan/toc.md` |
| 4 | Writer ×M | Write sections in parallel (one per ToC entry) | `draft/_sections/NN_*.md` |
| 5 | Editor | Merge all sections into cohesive document | `draft/v1.md` |
| 6 | Critic | Review → APPROVED or REVISE (max 2 loops) | `draft/_review.md` |
| 7 | Orchestrator | Generate PNGs via PaperBanana, embed in draft | `illustrations/*.png` + `illustrations/_manifest.md` |
| 8 | — | Delivery: stats, paths, next steps | — |

**Validation gates** at each phase: word count checks, file existence, structural integrity. Retry up to 2× if quality is insufficient.

### Parameters

All parameters are **optional** — sensible defaults are applied.

| Parameter | Values | Default |
|-----------|--------|---------|
| **Size** | `brief` (15–20p), `standard` (30–40p), `detailed` (60–100p) | `standard` |
| **Language** | Any | Auto-detected from query |
| **Document type** | `comparison`, `overview`, `sota`, `report` | Auto-detected |
| **Illustration mode** | `pipeline` (full PaperBanana cycle), `direct` (single API call), `none` | `pipeline` |

### Research agents

| Agent | Model | Role |
|-------|-------|------|
| **Research Orchestrator** | Sonnet 4.6 | Entry point, deterministic pipeline via `research_pipeline_runner.py` |
| **Researcher** | Sonnet 4.6 | Per-subtopic deep web search + content extraction (writes files directly) |
| **Analyst** | Sonnet 4.6 | Per-subtopic structure analysis |

**Search cascade** (when Tavily quota exceeded): Tavily → GitHub search (repos + code) → HuggingFace (papers + docs) → `fetch_webpage` for extraction.

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
| `web` | Orchestrator (direct) | Fetches web pages via `fetch_webpage`, extracts content |
| `confluence` | Orchestrator (direct) | Reads Confluence pages via MCP REST API |

### Phases

| Phase | Agent | Action | Output |
|-------|-------|--------|--------|
| 0 | Orchestrator | Parse request → `params.md` with `## Sources` | `research/_plan/params.md` |
| 1a | Orchestrator | Fetch web sources directly | `research/{area}/extract_*.md` |
| 1b | Orchestrator | Fetch Confluence pages via MCP | `research/{area}/extract_*.md` |
| 1c | Source Analyzer ×N | Analyze code / docs / config in parallel | `research/{area}/extract_*.md` |
| 2 | Arch Assessor ×N | Per-area assessment: patterns, tech debt, dependencies | `research/{area}/_assessment.md` |
| 3 | Solution Architect | Design 2–3 architecture options with trade-offs | `research/_plan/_proposals.md` |
| 4 | Planner | Build ToC for proposal document | `research/_plan/toc.md` |
| 5 | Writer ×M | Write sections in parallel | `draft/_sections/NN_*.md` |
| 6 | Editor | Merge into cohesive document | `draft/v1.md` |
| 7 | Critic | Review with architecture-specific criteria (max 2 loops) | `draft/_review.md` |
| 8 | Orchestrator | Generate architecture diagrams via PaperBanana | `illustrations/*.png` + `illustrations/_manifest.md` |
| 9 | — | Delivery + optional Confluence publish / PDF export | — |

### Architecture-specific agents

| Agent | Model | Role |
|-------|-------|------|
| **Architecture Orchestrator** | Sonnet 4.6 | Entry point, handles web/Confluence I/O, runs PaperBanana |
| **Source Analyzer** | Sonnet 4.6 | Scans code, docs, configs → structured extracts |
| **Arch Assessor** | Sonnet 4.6 | Per-area architecture assessment (patterns, debt, risks) |
| **Solution Architect** | Opus 4.6 | Synthesizes assessments → 2–3 proposals with recommendation |

---

## Core Design Principles

**Files = Protocol.** Agents communicate only through files on disk. No in-memory state sharing.

**Folders = Routing.** Each subtopic (research) or source area (architecture) gets its own folder under `research/`.

**Orchestrator = Dumb Scheduler.** The Python state machine (`research_pipeline_runner.py` / `arch_pipeline_runner.py`) decides the next phase. The orchestrator agent just executes.

**Sub-agents return text → Orchestrator writes files.** Most pipeline agents return markdown text. The orchestrator writes it to `output_file` and verifies. **Exception:** Researcher agents (Phase 1) write `_links.md` and `extract_*.md` files directly to enable parallel search + extraction.

**Deterministic phases with retry.** Each phase has validation gates — word counts, file existence, structural integrity. Up to 2 automatic retries if quality thresholds are not met.

**Parallel sub-agent execution.** Multiple `runSubagent` calls in one tool-call batch run concurrently. Phases 1, 2, 4 (and arch Phase 1c, 2, 5) launch agents in parallel.

---

## PaperBanana Illustration System

Both pipelines use **PaperBanana** (`llmsresearch/paperbanana`) to generate publication-quality PNG diagrams — no Mermaid, no ASCII art, no screenshots.

| Mode | When to use | Command |
|------|-------------|---------|
| Full pipeline (default) | All illustration types, best quality | `paperbanana_generate.py "desc" "output.png" --context "text" --critic-rounds 2` |
| `--direct` | Quick generation, single API call (~40s) | `paperbanana_generate.py "desc" "output.png" --direct` |

**Models:** `gpt-5.2` (VLM: Planner/Stylist/Critic) + `gpt-image-1.5` (Visualizer). Configurable via `TEXT_MODEL` / `IMAGE_MODEL` env vars.

**Pipeline stages:** Retriever → Planner → Stylist → Visualizer ↔ Critic (2 refinement rounds). Takes 3–5 min per illustration.

**Visual style:** NeurIPS academic aesthetic — flat vector, 2D, white background, pastel palette, clean typography.

**Placeholder format** (written by Writer, processed by Orchestrator at illustration phase):
```markdown
<!-- ILLUSTRATION: type="architecture", section="§2", description="..." -->
```

---

## Utility Scripts

| Script | Purpose |
|--------|---------|
| `extract_url.py` | Download + extract text from URL → write structured extract file. SSRF-safe (HTTPS/HTTP only). |
| `merge_sections.py` | Deterministic merge of `draft/_sections/*.md` → `draft/v1.md` (sorted by numeric prefix). |
| `validate_agents.py` | Validate all `.agent.md` and `.instructions.md` for structural correctness, cross-references, phase numbers. |

---

## Publishing

### PDF Export
```
@pdf-exporter
Export generated_docs_20260310_120000/draft/v1.md to PDF
```
Uses WeasyPrint with custom CSS — A4, styled headings, zebra tables, image borders, numbered pages.

### Confluence Publish
```
@confluence-publisher
Publish generated_arch_20260310_150000/draft/v1.md
to space=ARCH, title=LLM Orchestrator Proposal
```
Images uploaded via **REST API with Bearer token** (MCP cannot upload images). Requires `CONFLUENCE_URL`, `CONFLUENCE_TOKEN` env vars.

---

## Project Structure

```
.github/
  agents/                       # 15 agent definitions
    research-orchestrator.agent.md   # Pipeline 1 entry point (deterministic)
    architecture-orchestrator.agent.md  # Pipeline 2 entry point (deterministic)
    researcher.agent.md          # URL discovery + content extraction
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
  instructions/                  # Per-agent instruction files
  scripts/
    research_pipeline_runner.py   # Research pipeline state machine
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
├── pipeline.log                 # Automatic debug trace (loguru)
├── research/
│   ├── _plan/
│   │   ├── params.md            # Topic, audience, subtopics (Phase 0)
│   │   └── toc.md               # Unified Table of Contents (Phase 3)
│   └── {subtopic_slug}/         # One folder per subtopic
│       ├── _links.md            # Discovered URLs (Phase 1)
│       ├── extract_1.md         # Full extracted content (Phase 1)
│       ├── extract_N.md
│       └── _structure.md        # Analyst's depth assessment (Phase 2)
├── draft/
│   ├── _sections/
│   │   ├── 01_introduction.md   # Individual sections (Phase 4)
│   │   └── NN_slug.md
│   ├── v1.md                    # Merged document (Phase 5)
│   └── _review.md               # Critic's verdict (Phase 6)
└── illustrations/
    ├── _manifest.md             # Diagram metadata and prompts used
    └── diagram_*.png            # Generated illustrations (Phase 7)
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

Open your project, then `File → Add Folder to Workspace…` → select the cloned `deep-analyst` folder. Save the workspace (`File → Save Workspace As…`). Now all 15 agents are available in Copilot Chat alongside your project files.

**Option B — Git submodule (recommended for teams):**

```bash
# From your project root:
git submodule add https://github.com/antonchirikalov/deep-analyst.git .deep-analyst
git commit -m "Add deep-analyst as submodule"
```

Then create (or update) a `.code-workspace` file at your project root:

```jsonc
// my-project.code-workspace
{
  "folders": [
    { "path": "." },
    { "path": ".deep-analyst" }
  ]
}
```

Open the workspace file in VS Code (`File → Open Workspace from File…`) — all 15 agents become available in Copilot Chat alongside your project code.

**For teammates cloning the repo:**

```bash
git clone --recurse-submodules https://github.com/your-org/your-project.git
# Or if already cloned without submodules:
git submodule update --init
```

**To update deep-analyst to latest version:**

```bash
cd .deep-analyst && git pull origin main && cd ..
git add .deep-analyst
git commit -m "Update deep-analyst"
```

> **Tip:** Add `generated_docs_*` and `generated_arch_*` to your project's `.gitignore` — pipeline output folders should not be committed.

**Option C — Symlink `.github` into your project:**

```bash
# From your project root:
ln -s /path/to/deep-analyst/.github/agents .github/agents
ln -s /path/to/deep-analyst/.github/instructions .github/instructions
ln -s /path/to/deep-analyst/.github/scripts .github/scripts
ln -s /path/to/deep-analyst/.github/skills .github/skills
```

> **Note:** Option A is simplest for solo use, Option B is best for teams (version-locked, reproducible). Option C works but symlinks are fragile across machines.

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
