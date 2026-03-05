---
description: Three-phase illustration generation pipeline for Illustrator agent — Plan, Generate candidates, Select best.
---

# Generation Pipeline

## Overview

The Illustrator uses a three-phase pipeline inspired by PaperBanana:

```
Phase 1: Plan (descriptions + prompts) → Phase 2: Generate (parallel candidates) → Phase 3: Select (pick best)
```

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
5. For each illustration, combine the Analyst's description with the PaperBanana Golden Schema to write 2–3 prompt variations.
   **Critical:** Add `"All visible text labels and annotations in the image must be in {language}."` to every prompt (language passed by Orchestrator).

| Aspect | Variation A | Variation B | Variation C |
|--------|-----------|-----------|-----------|
| **Composition** | Horizontal (LR) | Vertical (TB) | Radial |
| **Detail level** | Minimal, clean | Medium with annotations | Detailed with explanations |
| **Label style** | Short labels | Full names | Icons + labels |

4. Record the plan internally before proceeding to generation.

## Phase 2: Generate (Parallel)

Generate 2–3 PNG candidates using the image-generator skill:

### Single candidate:
```bash
python3 .github/skills/image-generator/scripts/generate_image.py "Academic diagram: [description]" "illustrations/diagram_N_a.png"
```

### Multiple candidates via JSON:
Create a JSON file with prompt variations, then:
```bash
python3 .github/skills/image-generator/scripts/generate_image.py prompts_diagram_N.json illustrations diagram_N
```

The JSON file format:
```json
[
  "Academic diagram: transformer architecture, horizontal layout, minimal labels, clean white background",
  "Academic diagram: transformer architecture, vertical layout, detailed annotations, clean white background",
  "Academic diagram: transformer architecture, radial layout, icons and labels, clean white background"
]
```

## Phase 3: Select

1. Review all generated candidates by comparing prompt intent to section goals
2. Select the best candidate based on:
   - How well the composition matches the section's information hierarchy
   - Clarity and readability of the visual
   - Alignment with the academic style
3. Rename selected candidate: `diagram_N_b.png` → `diagram_N.png`
4. Clean up non-selected candidates (optional, configurable)
5. Create/update `illustrations/_manifest.md`

## Why No Vision-Critique?

Vision evaluation via API is expensive and doubles latency. Instead, we generate multiple candidates with different prompts (cheaper than critique+refine) and pick the best one by prompt quality. Empirically: 3 candidates yield better results than 1 candidate + 2 rounds of critique.

## Re-run Behavior

When Orchestrator requests re-generation (after Critic flagged ILLUSTRATION_ISSUES: YES):
1. Read the Critic's feedback to identify which diagrams need improvement
2. Only regenerate flagged diagrams — keep approved ones
3. Update `_manifest.md` with new entries
