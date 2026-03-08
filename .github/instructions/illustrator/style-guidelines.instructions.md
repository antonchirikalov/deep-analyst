```instructions
---
description: PaperBanana-style academic illustration guidelines and structured prompt engineering for the Illustrator agent. Based on the PaperBanana framework (Zhu et al., 2026).
---

# Style Guidelines — PaperBanana Method

## Core Philosophy

All illustrations follow the **PaperBanana aesthetic standard**: NeurIPS-quality flat-vector academic diagrams with clean white backgrounds, pastel colors, and clear visual hierarchy.

**Two generation modes with different prompt strategies:**
- **Direct mode (default):** Short prompts (2-4 sentences). The script auto-prepends style instructions. Focus on visual structure and key elements — verbose prompts cause text-heavy output.
- **Pipeline mode** (statistical/data plots only): Full structured zone-based Golden Schema prompt where every element, connection, color, and spatial position is explicitly specified.

## PaperBanana NeurIPS 2025 Aesthetic Rules

### Art Style (Mandatory)
- **Flat vector graphics** — clean geometric shapes, distinct outlines
- **Strictly 2D** with optional subtle isometric elements for depth
- **Clean white background** — no gradients, no textures
- **Soft pastel fills** with thin dark outlines (0.5–1pt)
- **NOT hand-drawn, NOT photorealistic, NOT 3D render**
- **NO heavy shadows, NO gradients on shapes** (subtle drop shadows OK on key elements)
- Professional academic aesthetic — suitable for NeurIPS/CVPR/ICML publications

### Color Palette — Professional Pastel
Use **3–5 colors** per diagram from this curated NeurIPS 2025 palette:

| Role | Primary | Secondary | Hex Codes |
|------|---------|-----------|-----------|
| **System A / Input** | Azure Blue | Light Azure | #4A90D9, #B8D4F0 |
| **System B / Process** | Soft Purple | Lavender | #7B5EA7, #C9B8E8 |
| **System C / Output** | Coral Orange | Peach | #E8734A, #F5C4A1 |
| **Neutral / Structure** | Slate Grey | Light Grey | #5B6770, #E0E3E6 |
| **Accent / Highlight** | Mint Green | Light Mint | #4AAEA8, #B8E4E0 |
| **Warning / Negative** | Muted Red | Light Rose | #C75450, #F0C4C2 |

### Typography in Diagrams
- Short labels only (2–4 words max per element)
- Clear sans-serif rendering
- No overlapping text — labels must be inside or clearly adjacent to their element
- Use icons/symbols instead of long text where possible

### Shapes & Containers
- **Rounded rectangles** (corner radius 8–12px) for components/modules
- **Circles/ovals** for data points, inputs, decision nodes
- **Hexagons** for agents/processes
- **Diamonds** for decision points
- **Arrows**: thin (1–2pt), with clear direction, slight curve preferred over straight lines
- Borders: thin dark outlines (#333 or #555), 0.5–1pt
- Background fills: pastel versions of the assigned color

### Layout Principles
- **Zone-based composition**: divide the canvas into logical zones (left/center/right or top/bottom)
- **Clear visual hierarchy**: primary flow top-to-bottom or left-to-right
- **Balanced white space**: no dead zones, no cramped regions
- **Consistent spacing**: equal gaps between parallel elements
- **LaTeX-compatible**: rectangular composition, no protruding elements

## Prompt Formats by Mode

### Direct Mode Prompt Format (DEFAULT — for most illustrations)

Keep it **short** — 2-4 sentences, ~50-100 words. The script auto-prepends vector-style instructions.

```
[Visual structure: columns/rows/hierarchy/flow direction].
[Key blocks and their colors].
[Connections: arrows, lines, flow].
[Bottom/side: integration or legend elements].
```

**Example (architecture comparison):**
```
Three-column comparison of AI platforms. LEFT 'Copilot' in blue with hub-spoke
model icons and cloud sandbox. CENTER 'Claude Code' in orange with Lead Agent,
three Teammate blocks, and Shared Task Board. RIGHT 'Codex CLI' in green with
App Server hub and client connections. Bottom: shared MCP protocol bus.
```

**Why short?** Long verbose prompts (zone-by-zone specs with exact text, positions, pixel sizes) cause the image model to render TEXT BLOCKS instead of graphics — producing ugly ASCII-art monospace output.

### Pipeline Mode Prompt Format (statistical plots / data viz ONLY)

> ⚠️ Do NOT use this format for architecture/comparison/flowchart diagrams — it produces text-heavy output.

For pipeline mode (`--context`, no `--direct`), use the full PaperBanana Golden Schema. Every prompt MUST use this structured format:

```
---BEGIN PROMPT---

[Style & Meta-Instructions]
High-fidelity scientific schematic, technical vector illustration, clean white
background, distinct boundaries, academic NeurIPS publication style. High resolution,
strictly 2D flat design with subtle isometric elements. Professional pastel color
palette. No meta-labels or structural instructions visible in the image.

[LAYOUT CONFIGURATION]
Selected Layout: [e.g., Three-Column Comparison / Pipeline Flow / Radial Hub]
Composition Logic: [1-2 sentences describing the overall spatial arrangement]
Color Palette: [List 3-5 colors with roles]

[ZONE 1: POSITION - LABEL]
Container: [Shape, size, color]
Internal Elements: [List every icon, sub-box, label inside this zone]
Connections: [Arrows/lines from this zone to others]

[ZONE 2: POSITION - LABEL]
Container: [...]
Internal Elements: [...]
Connections: [...]

[ZONE N: POSITION - LABEL]
...

[GLOBAL ANNOTATIONS]
[Any spanning labels, legends, title bar, or comparison indicators]

---END PROMPT---
```

### Critical Prompt Rules (from PaperBanana)
1. **Be exhaustively specific**: Describe EVERY element, connection, and spatial relationship. Vague = bad.
2. **Define "objects" inside each zone**: Use concrete terms (icons, grids, boxes), NOT abstract concepts.
3. **Explicit connections**: Describe arrow types ("curved arrow from Zone 1 to Zone 3", "dashed line between...").
4. **No meta-labels in output**: Words like "ZONE 1", "INPUT", "OUTPUT" are structural instructions for the model, not text to render.
5. **Vary prompt candidates** by: layout orientation, detail density, icon style, color emphasis.

## PaperBanana Pipeline for Illustrator Agent

### Phase 1: Plan (Planner role)
1. Read the document section to illustrate
2. Identify key concepts, relationships, and visual hierarchy
3. Write a **detailed textual description** (200–400 words) covering:
   - Every element and what it represents
   - Every connection between elements
   - Spatial layout and grouping logic
   - Information flow direction

### Phase 2: Style (Stylist role)
1. Take the plan description and apply NeurIPS 2025 aesthetic rules
2. Assign specific colors from the pastel palette
3. Choose shapes/containers for each element type
4. Specify exact spatial zones
5. Output the **Golden Schema** structured prompt

### Phase 3: Generate (Visualizer role)
1. Generate 2–3 candidates per diagram using the Golden Schema prompt
2. Each candidate varies: layout orientation, detail level, icon density

### Phase 4: Critique & Select
1. Compare candidates against the plan description
2. Check: visual hierarchy, color harmony, label clarity, balanced composition
3. Select the best candidate

## What to Visualize by Document Type

| Document Type | Recommended Illustrations |
|--------------|----------------------|
| Comparative Analysis | Architecture diagram per approach + Visual comparison infographic + Decision flowchart |
| Technology Overview | Architecture diagram + Dataflow/pipeline visualization + Sequence/flow diagram |
| State of the Art | Visual evolution timeline + Methods taxonomy map + Mindmap of current approaches |
| Research Report | Methodology visualization + Results comparison + Approach comparison diagram |

## Anti-Patterns

- ❌ Vague one-sentence prompts ("Draw an architecture diagram")
- ❌ Dark backgrounds, neon colors, heavy gradients
- ❌ 3D renders, photorealistic style, hand-drawn aesthetic
- ❌ Text-heavy illustrations (labels > 4 words)
- ❌ Protruding elements outside the main composition frame
- ❌ Default software styles (Excel charts, basic Matplotlib)
- ❌ Identical prompts for different candidates
```
