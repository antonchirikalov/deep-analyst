#!/usr/bin/env python3
"""OpenAI gpt-image-1 wrapper for academic illustration generation.

Supports single image generation and batch candidate generation with prompt variations.
Reads OPENAI_API_KEY from .env file in project root.
"""

import base64
import json
import os
import sys

from dotenv import load_dotenv
import openai

load_dotenv()  # reads .env from project root
client = openai.OpenAI()  # OPENAI_API_KEY from env


def generate_diagram(prompt: str, output_path: str, size: str = None, quality: str = None) -> str:
    """Generate a single diagram via gpt-image-1.

    Args:
        prompt: Text description of the diagram to generate.
        output_path: Path to save the generated PNG.
        size: Image size (default from IMAGE_SIZE env or 1536x1024).
        quality: Image quality (default from IMAGE_QUALITY env or high).

    Returns:
        The output path of the generated image.
    """
    size = size or os.environ.get("IMAGE_SIZE", "1536x1024")
    quality = quality or os.environ.get("IMAGE_QUALITY", "high")
    model = os.environ.get("IMAGE_MODEL", "gpt-image-1")

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    response = client.images.generate(
        model=model,
        prompt=prompt,
        n=1,
        size=size,
        quality=quality,
        background="opaque",
        output_format="png",
    )

    # gpt-image-1 returns base64
    image_data = base64.b64decode(response.data[0].b64_json)
    with open(output_path, "wb") as f:
        f.write(image_data)

    return output_path


def generate_candidates(prompts: list[str], output_dir: str, base_name: str, size: str = None) -> list[dict]:
    """Generate N candidates from different prompts.

    Called sequentially (OpenAI API doesn't support batch),
    but Illustrator agent can call the script multiple times via run_in_terminal.

    Args:
        prompts: List of 2–3 prompt variations.
        output_dir: Save directory.
        base_name: Base filename (e.g., diagram_1).
        size: Image size override.

    Returns:
        List of dicts with file path, prompt, and variant suffix.
    """
    os.makedirs(output_dir, exist_ok=True)
    results = []
    suffixes = ["a", "b", "c", "d", "e"]

    for i, prompt in enumerate(prompts):
        suffix = suffixes[i] if i < len(suffixes) else str(i)
        output_path = os.path.join(output_dir, f"{base_name}_{suffix}.png")
        generate_diagram(prompt, output_path, size)
        results.append({"file": output_path, "prompt": prompt, "variant": suffix})
        print(f"Generated candidate {suffix}: {output_path}")

    return results


if __name__ == "__main__":
    if len(sys.argv) == 3:
        # Single candidate mode: python generate_image.py "prompt" "output.png"
        prompt = sys.argv[1]
        output = sys.argv[2]
        generate_diagram(prompt, output)
        print(f"Generated: {output}")
    elif len(sys.argv) == 4:
        # N candidates mode: python generate_image.py prompts.json output_dir base_name
        with open(sys.argv[1]) as f:
            prompts = json.load(f)
        results = generate_candidates(prompts, sys.argv[2], sys.argv[3])
        print(json.dumps(results, indent=2))
    else:
        print("Usage:")
        print("  Single:  python generate_image.py 'prompt' 'output.png'")
        print("  Multi:   python generate_image.py prompts.json output_dir base_name")
        sys.exit(1)
