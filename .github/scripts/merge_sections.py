#!/usr/bin/env python3
"""Merge section files into a single document.

Replaces Editor sub-agent: deterministic concatenation eliminates
~38K tokens of double-write (sub-agent return + create_file).

Usage:
    python3 merge_sections.py <base_folder>

Output to stdout: "✓ Merged N sections → draft/v1.md (XXXX words)"
"""

import re
import sys
from pathlib import Path


def merge(base_folder: str) -> None:
    base = Path(base_folder).resolve()
    sections_dir = base / "draft" / "_sections"
    params_file = base / "research" / "_plan" / "params.md"

    if not sections_dir.exists():
        print("ERROR: No _sections directory", file=sys.stderr)
        sys.exit(1)

    # Sort by numeric prefix (01_, 02_, ...)
    section_files = sorted(sections_dir.glob("*.md"), key=lambda f: f.stem)
    if not section_files:
        print("ERROR: No section files found", file=sys.stderr)
        sys.exit(1)

    # Read title from params
    title = "Research Document"
    if params_file.exists():
        text = params_file.read_text(encoding="utf-8")
        m = re.search(r'-\s+\*\*(?:Topic|Тема):?\*\*:?\s*(.+)', text, re.IGNORECASE)
        if m:
            title = m.group(1).strip()

    # Build document: title + all sections
    parts = [f"# {title}\n"]
    for sf in section_files:
        content = sf.read_text(encoding="utf-8").strip()
        if content:
            parts.append(content)

    document = "\n\n".join(parts)

    # Write
    output = base / "draft" / "v1.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document, encoding="utf-8")

    wc = len(document.split())
    print(f"✓ Merged {len(section_files)} sections → draft/v1.md ({wc} words)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: merge_sections.py <base_folder>", file=sys.stderr)
        sys.exit(1)
    try:
        merge(sys.argv[1])
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
