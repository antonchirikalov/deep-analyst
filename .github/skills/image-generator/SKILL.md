---
name: image-generator
description: Generates publication-quality academic illustrations using the PaperBanana package (llmsresearch/paperbanana) — a multi-agent pipeline (Retriever → Planner → Stylist → Visualizer ↔ Critic) with OpenAI as the provider.
---

# Image Generator (PaperBanana Pipeline)

## When to use
- When Illustrator agent needs to generate academic diagrams
- When regenerating specific diagrams after Critic feedback

## CRITICAL: Choosing the right mode

### Direct generation (RECOMMENDED for architecture/technical diagrams)
```bash
python3 .github/skills/image-generator/scripts/paperbanana_generate.py "[description]" "illustrations/diagram_N.png" --direct
```

**Use `--direct` for:** architecture diagrams, system overviews, flowcharts, comparison layouts, any diagram with boxes/arrows/structural elements.

`--direct` calls gpt-image-1.5 with a concise prompt. This produces clean graphical illustrations.

**Prompt guidelines for `--direct`:**
- Keep prompts SHORT (2-4 sentences max)
- Focus on visual structure, not exact text labels
- Describe shapes, colors, spatial layout
- Say "professional vector-style technical diagram" or "clean infographic style"
- Do NOT list exact text for every label — the model will generate appropriate labels
- Do NOT write multi-paragraph layout specs — this causes ASCII-art output

### Full PaperBanana pipeline (for data visualizations / methodology figures only)
```bash
python3 .github/skills/image-generator/scripts/paperbanana_generate.py "[illustration description]" "illustrations/diagram_N.png" --context "[methodology text or section content]"
```

The wrapper calls the real `paperbanana` package (`PaperBananaPipeline.generate()`) with OpenAI provider:
- **Phase 1 (Linear Planning):** Retriever → Planner → Stylist
- **Phase 2 (Iterative Refinement):** Visualizer ↔ Critic (default 2 rounds)

VLM agent (Planner/Stylist/Critic) uses `gpt-5.2`, image generation (Visualizer) uses `gpt-image-1.5`.

⚠️ **WARNING:** The pipeline Planner generates extremely verbose layout descriptions. For architecture/technical diagrams, this causes the Visualizer to produce text-heavy ASCII-art-like output instead of clean graphics. Use `--direct` mode for these.

## Configuration

The script reads from `.env` file in project root:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | (required) | OpenAI API key for all agents |
| `TEXT_MODEL` | `gpt-5.2` | VLM model for Planner/Stylist/Critic |
| `IMAGE_MODEL` | `gpt-image-1.5` | Image generation model |
| `MAX_CRITIC_ROUNDS` | `2` | Visualizer-Critic refinement iterations |

## Dependencies

```
pip install "paperbanana[openai]" python-dotenv
```

## Output
- Generates one PNG at the specified path (copied from PaperBanana's `outputs/` dir)
- All intermediate iterations and metadata saved by PaperBanana in `outputs/`
