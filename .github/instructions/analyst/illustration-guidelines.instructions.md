````instructions
---
description: Illustration placeholder guidelines for Analyst — how to mark sections for PaperBanana PNG generation by the Illustrator agent.
---

# Illustration Guidelines (PaperBanana)

All visual diagrams in documents are generated as **PNG illustrations** by the Illustrator agent using the PaperBanana method. The Analyst does NOT create any inline diagrams — instead, the Analyst places detailed **illustration placeholders** in the draft for the Illustrator to process in Phase 3.

## Required Illustrations by Document Type

| Document Type | Required Illustrations (3–5 placeholders) |
|--------------|------------------------------------------|
| Comparative Analysis | 1) Architecture diagram per approach 2) Visual comparison infographic 3) Decision flowchart "when to choose what" |
| Technology Overview | 1) Architecture diagram 2) Dataflow/pipeline visualization 3) Sequence/flow diagram |
| State of the Art | 1) Visual evolution timeline 2) Methods taxonomy map 3) Mindmap of current approaches |
| Research Report | 1) Methodology visualization 2) Results comparison 3) Approach comparison diagram |

## Illustration Placeholder Format

For every section that needs a visual diagram, the Analyst MUST insert this HTML comment placeholder:

```markdown
<!-- ILLUSTRATION: type=[architecture|comparison|pipeline|infographic|conceptual|flowchart|timeline|mindmap], section="§N. Section Title", description="Detailed description of what should be visualized: every key element, every connection, spatial layout, information flow, color logic. The MORE detail, the BETTER the illustration. Minimum 200 characters." -->

*[Рис. N. Caption describing the illustration]*
```

### Type Reference

| Type | When to Use |
|------|------------|
| `architecture` | System design, component diagrams, platform structure |
| `comparison` | Side-by-side analysis, radar charts, feature matrices |
| `pipeline` | Data flows, processing stages, agent coordination |
| `infographic` | Summary visuals, statistics, key metrics |
| `conceptual` | Abstract ideas, relationships, visual metaphors |
| `flowchart` | Decision trees, process flows, algorithms |
| `timeline` | Evolution, version history, milestones |
| `mindmap` | Domain overview, taxonomy, approach classification |

## Example Placeholders

### Architecture Comparison (Comparative Analysis)
```markdown
<!-- ILLUSTRATION: type=architecture, section="§3. Architecture Comparison", description="Three-column comparison showing GitHub Copilot (left column: hub-spoke with VS Code IDE at center, extensions radiating out, MCP servers below), Claude Code (center column: linear CLI pipeline — terminal input → agent core → tool calls → output), and OpenAI Codex (right column: cloud-async architecture — GitHub issue input → cloud sandbox → parallel containers → PR output). Each column: top=input source, middle=agent processing core with internal components, bottom=output artifacts. Arrows show tool connections. Color: blue for Copilot, purple for Claude, orange for Codex. Rounded rectangles for components, hexagons for agent cores." -->

*[Рис. 1. Сравнение архитектур трёх платформ]*
```

### Decision Flowchart (Conclusions)
```markdown
<!-- ILLUSTRATION: type=flowchart, section="§7. Conclusions and Recommendations", description="Decision tree for choosing an AI agent platform. Root node: 'Выбор платформы'. First branch: 'Среда разработки?' → 'VS Code/IDE' leads to 'GitHub Copilot Agents', 'Терминал/CLI' leads to second branch. Second branch: 'Тип задач?' → 'Интерактивная разработка' leads to 'Claude Code', 'Пакетная обработка/CI' leads to 'OpenAI Codex'. Each leaf node colored: blue=Copilot, purple=Claude, orange=Codex. Diamond shapes for decision nodes, rounded rectangles for final recommendations." -->

*[Рис. 3. Дерево выбора платформы]*
```

### Pipeline Visualization (Technology Overview)
```markdown
<!-- ILLUSTRATION: type=pipeline, section="§4. Architecture / How It Works", description="Horizontal pipeline showing 5 stages: Input (user prompt in terminal) → Context Gathering (file reads, grep, semantic search — show 3 small tool icons) → Agent Reasoning (central large hexagon with 'LLM Core' label, thought bubbles) → Tool Execution (parallel branch: file edit, terminal command, web search — 3 parallel arrows) → Output (modified files, terminal output). Arrows flow left-to-right. Feedback loop arrow from Output back to Context Gathering. Pastel blue for input/output, purple for reasoning, green for tools." -->

*[Рис. 2. Конвейер обработки запросов]*
```

## Rules for Placeholders

1. **Place at the exact position** where the illustration should appear in the document
2. **`type`** — must match one of the types in the reference table above
3. **`description`** — must be **200+ characters** with:
   - Every key element (nodes, boxes, labels)
   - Every connection (arrows, lines, their direction)
   - Spatial layout (left-to-right, top-to-bottom, columns, radial)
   - Color logic (which color for which element/category)
   - Shape preferences (rectangles, hexagons, diamonds, circles)
4. **Caption line** — `*[Рис. N. Caption]*` below for text reference
5. **Quantity** — every document MUST have **3–5 illustration placeholders**
6. **DO NOT** create any inline code-based diagrams — ALL visuals are PaperBanana PNGs

## Scaling by Document Size

| Document Size | Illustration Count |
|--------------|-------------------|
| Short (~1500–2500 words) | 2–3 placeholders |
| Standard (~3000–5000 words) | 3–4 placeholders |
| Detailed (~5000–8000 words) | 4–5 placeholders |

## What Makes a Good Description

**Bad** (too vague — will produce poor results):
> "Architecture diagram of the system"

**Good** (specific elements, connections, layout):
> "Three-layer architecture: top layer has 3 input sources (API, CLI, Web UI) as rounded boxes in a row. Middle layer: central hexagon 'Processing Engine' with 4 internal modules (Parser, Validator, Executor, Cache) shown as smaller boxes inside. Bottom layer: 3 output targets (Database, File System, API Response). Vertical arrows from inputs to engine, from engine to outputs. Color: blue for inputs, purple for processing, green for outputs. Dashed arrows for optional connections."

The PaperBanana principle: **vague or unclear specifications will only make the generated figure worse, not better.**

````
