#!/usr/bin/env python3
"""Extract content from a URL and write directly to a file.

Eliminates double-write: content goes to disk without passing through
the orchestrator's context window.

Usage:
    python3 extract_url.py <url> <output_file>

Output to stdout: "✓ {filename} — {word_count} words"
Exit codes: 0 = success, 1 = failure
"""

import re
import sys
from pathlib import Path
from urllib.parse import urlparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: pip install requests beautifulsoup4", file=sys.stderr)
    sys.exit(1)


def extract(url: str, output_path: str) -> None:
    # Validate URL scheme to prevent SSRF
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; deep-analyst/1.0)",
    }
    resp = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove non-content elements
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    # Extract title
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    elif soup.find("h1"):
        title = soup.find("h1").get_text(strip=True)

    # Get main content (prefer semantic containers)
    main = (
        soup.find("main")
        or soup.find("article")
        or soup.find(class_=re.compile(r"content|article|post|entry", re.I))
    )
    if main:
        text = main.get_text(separator="\n", strip=True)
    else:
        text = soup.get_text(separator="\n", strip=True)

    # Clean up whitespace
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    text = "\n\n".join(lines)

    wc = len(text.split())

    # Format as extract file
    content = f"# Extract: {title}\nSource: {url}\nWords: ~{wc}\n\n{text}\n"

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")

    print(f"✓ {out.name} — {wc} words")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: extract_url.py <url> <output_file>", file=sys.stderr)
        sys.exit(1)
    try:
        extract(sys.argv[1], sys.argv[2])
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
