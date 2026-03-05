---
description: Two-phase illustration generation pipeline for Illustrator agent — Plan one optimized prompt, Generate one PNG per illustration.
---

# Generation Pipeline

## Overview

The Illustrator uses a two-phase pipeline:

```
Phase 1: Plan (one optimized prompt per illustration) → Phase 2: Generate (one PNG each)
```

We generate **one image per illustration** with a single well-crafted prompt. Multi-candidate generation is wasteful: without vision-critique the "selection" is blind, and prompt variations (horizontal vs vertical layout) produce marginal differences that don't justify 2–3x the API cost.

## Phase 1: Plan

1. Read the draft document (`draft/vN.md`)
2. **Extract all `<!-- ILLUSTRATION: type=..., section=..., description="..." -->` placeholders** left by the Analyst
3. For each placeholder, parse:
   - `type` — architecture, comparison, pipeline, infographic, conceptual
   - `section` — which document section this belongs to
   - `description` — Analyst's detailed description of what to visualize (200+ chars)
4. If no placeholders found, fall back to independent identification:
   - Architecture/system design sections
   - Pipeline/workflow descriptions
   - Comparison sections with complex relationships
   - Abstract concepts that benefit from visual representation
5. For each illustration, craft **one optimized prompt** using the PaperBanana Golden Schema:
   - Use the Analyst's description as the primary input
   - Choose the best composition for the content type:
     - **Horizontal (LR)** — flows, pipelines, timelines, sequences (default for most)
     - **Vertical (TB)** — hierarchies, layered architectures, decision trees
     - **Radial** — comparisons, ecosystems, hub-spoke relationships
   - Include: all elements, connections/arrows, spatial layout, colors, shape preferences
   - Always end with: "Clean white background, no text overlapping elements"
6. Record the plan internally before proceeding to generation.

## Phase 2: Generate

Generate **one PNG per illustration**:

```bash
python3 .github/skills/image-generator/scripts/generate_image.py "Academic diagram: [description]" "illustrations/diagram_N.png"
```

Run one command per illustration. After all are generated, create `illustrations/_manifest.md`.

## Re-run Behavior

When Orchestrator requests re-generation (after Critic flagged ILLUSTRATION_ISSUES: YES):
1. Read the Critic's feedback to identify which diagrams need improvement
2. Only regenerate flagged diagrams — keep approved ones
3. Refine the prompt based on Critic's feedback
4. Update `_manifest.md` with new entries
