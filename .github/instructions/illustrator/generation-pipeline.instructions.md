---
description: Two-phase illustration generation pipeline for Illustrator agent — Plan one optimized prompt, Generate one PNG per illustration using the PaperBanana package (llmsresearch/paperbanana) with OpenAI provider.
---

# Generation Pipeline

## Overview

The Illustrator uses a two-phase pipeline:

```
Phase 1: Plan (parse placeholders, prepare description + context)
Phase 2: Generate (PaperBanana package: Retriever → Planner → Stylist → Visualizer ↔ Critic)
```

The `paperbanana` package handles prompt engineering, reference retrieval, aesthetic refinement, image generation, and iterative critique internally. The Illustrator's job is to **extract the right description and context** from the draft and feed them to the script.

## Phase 1: Plan

1. Read the final draft (`generated_docs_[TIMESTAMP]/draft/v1.md`)
2. **Extract all `<!-- ILLUSTRATION: type=..., section=..., description="..." -->` placeholders** left by the Writer
3. For each placeholder, parse:
   - `type` — architecture, comparison, pipeline, infographic, conceptual
   - `section` — which document section this belongs to
   - `description` — Writer's detailed description of what to visualize (200+ chars)
4. If no placeholders found, fall back to independent identification:
   - Architecture/system design sections
   - Pipeline/workflow descriptions
   - Comparison sections with complex relationships
   - Abstract concepts that benefit from visual representation
5. For each illustration, craft **one optimized prompt** using the PaperBanana Golden Schema:
   - Use the Writer's description as the primary input
   - Choose the best composition for the content type:
     - **Horizontal (LR)** — flows, pipelines, timelines, sequences (default for most)
     - **Vertical (TB)** — hierarchies, layered architectures, decision trees
     - **Radial** — comparisons, ecosystems, hub-spoke relationships
   - Include: all elements, connections/arrows, spatial layout, colors, shape preferences
   - Always end with: "Clean white background, no text overlapping elements"
6. Record the plan internally before proceeding to generation.

## Phase 2: Generate

### Step 1: Choose Generation Mode

For each illustration, select the mode based on type:

| Illustration Type | Mode | Command |
|---|---|---|
| `architecture`, `comparison`, `pipeline`, `flowchart`, `conceptual`, `infographic`, `timeline`, `mindmap` | **`--direct`** | `python3 .github/skills/image-generator/scripts/paperbanana_generate.py "[SHORT prompt]" "generated_docs_[TIMESTAMP]/illustrations/diagram_N.png" --direct` |
| `statistical_plot`, `methodology` (data-heavy charts) | **pipeline** | `python3 .github/skills/image-generator/scripts/paperbanana_generate.py "[description]" "generated_docs_[TIMESTAMP]/illustrations/diagram_N.png" --context "[section text]"` |

**Default: `--direct`** for everything except statistical/data plots.

### Step 2: Craft the Prompt

**For `--direct` mode (most illustrations):**

Keep prompts **SHORT** — 2-4 sentences, max ~100 words. The script auto-prepends vector-style instructions.

- Describe visual structure (columns, hierarchy, flow direction)
- Name key blocks with color categories (e.g., "blue for Copilot, orange for Claude")
- Describe connections briefly (arrows, lines)
- Do NOT enumerate exact text labels, positions, or pixel sizes
- Do NOT write the PaperBanana Golden Schema for direct mode — it causes text-heavy ASCII-art output

**For pipeline mode (statistical plots):**

Use the full PaperBanana approach — the Planner/Stylist/Critic cycle is optimized for data visualizations. Pass 200-500 words of section context via `--context`.

### Step 3: Generate

Run one command per illustration. After all are generated:

1. **EMBED ILLUSTRATIONS IN THE DOCUMENT** — this step is MANDATORY:

   **Path A — Placeholders exist:**
   Replace each `<!-- ILLUSTRATION: ... -->` placeholder in the draft (`generated_docs_[TIMESTAMP]/draft/v1.md`) with `![Рис. N](../illustrations/NN_name.png)` (path relative to `draft/v1.md` — resolves to `illustrations/` at the output folder root). **Keep the caption line** `*[Рис. N. Caption]*` that the Writer placed below the placeholder — only replace the HTML comment, not the caption.

   **Path B — No placeholders (fallback):**
   You MUST STILL embed illustrations. For each generated PNG:
   - Find the target section heading (H2 `##`) in `draft/v1.md`
   - Locate the end of the first paragraph after that heading
   - Use `replace_string_in_file` to insert `\n\n![Рис. N. Caption](../illustrations/NN_name.png)\n` right after that paragraph
   - Example: find `## 3. Architecture\n\nFirst paragraph text here.` and insert the image reference after the first paragraph

2. Create `generated_docs_[TIMESTAMP]/illustrations/_manifest.md`
3. **VERIFY:** Read v1.md and confirm every generated PNG is referenced. If any is missing, insert it.

**Output without embedded images = FAILED. Every PNG must appear as `![...]` in v1.md.**

## Re-run Behavior

When Orchestrator requests re-generation (after Critic flagged ILLUSTRATION_ISSUES: YES):
1. Read the Critic's feedback to identify which diagrams need improvement
2. Only regenerate flagged diagrams — keep approved ones
3. Refine the prompt based on Critic's feedback
4. Update `_manifest.md` with new entries
