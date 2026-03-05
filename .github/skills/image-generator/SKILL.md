---
name: image-generator
description: Generates publication-quality academic illustrations via OpenAI gpt-image-1. Supports single image generation and batch candidate generation with prompt variations. Use when the Illustrator agent needs to create PNG diagrams for research documents.
---

# Image Generator

## When to use
- When Illustrator agent needs to generate academic diagrams
- When creating illustration candidates for selection
- When regenerating specific diagrams after Critic feedback

## How to use

### Single image generation
```bash
python3 .github/skills/image-generator/scripts/generate_image.py "Academic diagram: [description]" "output_path.png"
```

### Batch candidate generation (via JSON file)
Create a JSON file with prompt variations:
```json
[
  "Academic diagram: transformer architecture, horizontal layout, minimal labels, white background",
  "Academic diagram: transformer architecture, vertical layout, detailed annotations, white background",
  "Academic diagram: transformer architecture, radial layout, icons + labels, white background"
]
```

Then generate all candidates:
```bash
python3 .github/skills/image-generator/scripts/generate_image.py prompts_diagram_1.json illustrations diagram_1
```

This creates `illustrations/diagram_1_a.png`, `diagram_1_b.png`, `diagram_1_c.png`.

## Configuration

The script reads from `.env` file in project root:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | (required) | OpenAI API key |
| `IMAGE_MODEL` | `gpt-image-1` | Image generation model |
| `IMAGE_SIZE` | `1536x1024` | Output image size |
| `IMAGE_QUALITY` | `high` | Generation quality |
| `CANDIDATES_PER_DIAGRAM` | `3` | Default candidates per diagram |

## Dependencies

```
pip install openai pillow python-dotenv
```

## Output
- Single mode: generates one PNG at the specified path
- Batch mode: generates N PNGs with suffixed filenames, prints JSON with file list
