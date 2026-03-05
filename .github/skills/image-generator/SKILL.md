---
name: image-generator
description: Generates publication-quality academic illustrations via OpenAI gpt-image-1. Supports single image generation and batch candidate generation with prompt variations. Use when the Illustrator agent needs to create PNG diagrams for research documents.
---

# Image Generator

## When to use
- When Illustrator agent needs to generate academic diagrams
- When regenerating specific diagrams after Critic feedback

## How to use

### Generate one illustration
```bash
python3 .github/skills/image-generator/scripts/generate_image.py "Academic diagram: [description]" "illustrations/diagram_N.png"
```

One call per illustration. Craft a single well-optimized prompt rather than generating multiple candidates — without vision-critique, candidate selection is blind and wastes API budget.

## Configuration

The script reads from `.env` file in project root:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | (required) | OpenAI API key |
| `IMAGE_MODEL` | `gpt-image-1` | Image generation model |
| `IMAGE_SIZE` | `1536x1024` | Output image size |
| `IMAGE_QUALITY` | `high` | Generation quality |


## Dependencies

```
pip install openai pillow python-dotenv
```

## Output
- Generates one PNG at the specified path
- Prints the output path on success
