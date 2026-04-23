#!/usr/bin/env python3
"""
Markdown → PDF converter with publication-quality styling.
Uses: markdown (MD→HTML) + weasyprint (HTML→PDF).
Supports: tables, images (absolute paths), headings, lists, code blocks, bold/italic.

Usage:
    python md_to_pdf.py <input.md> [output.pdf]
"""

import sys
import os
import logging
import re
import markdown
from weasyprint import HTML

logger = logging.getLogger(__name__)

# ── Publication-quality CSS ──────────────────────────────────────────────────
CSS = """
@page {
    size: A4;
    margin: 25mm 20mm 25mm 20mm;
    @bottom-center {
        content: counter(page);
        font-size: 9pt;
        color: #666;
    }
}
@page :first {
    @bottom-center {
        content: none;
    }
}

body {
    font-family: "Helvetica Neue", Helvetica, Arial, "Noto Sans", sans-serif;
    font-size: 11pt;
    line-height: 1.55;
    color: #1a1a1a;
    max-width: 100%;
}

/* ── Headings ── */
h1 {
    font-size: 20pt;
    font-weight: 700;
    color: #111;
    margin-top: 0;
    margin-bottom: 12pt;
    padding-bottom: 6pt;
    border-bottom: 2.5pt solid #2563eb;
    page-break-after: avoid;
}
h2 {
    font-size: 15pt;
    font-weight: 600;
    color: #1e3a5f;
    margin-top: 22pt;
    margin-bottom: 8pt;
    padding-bottom: 3pt;
    border-bottom: 1pt solid #cbd5e1;
    page-break-after: avoid;
}
h3 {
    font-size: 12.5pt;
    font-weight: 600;
    color: #334155;
    margin-top: 16pt;
    margin-bottom: 6pt;
    page-break-after: avoid;
}
h4 {
    font-size: 11pt;
    font-weight: 600;
    color: #475569;
    margin-top: 12pt;
    margin-bottom: 4pt;
}

/* ── Paragraphs ── */
p {
    margin-top: 0;
    margin-bottom: 8pt;
    text-align: justify;
    hyphens: auto;
}

/* ── Metadata block (bold lines at top) ── */
h1 + p strong {
    color: #475569;
}

/* ── Horizontal rules ── */
hr {
    border: none;
    border-top: 1pt solid #e2e8f0;
    margin: 18pt 0;
}

/* ── Tables ── */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 12pt 0 16pt 0;
    font-size: 9.5pt;
    line-height: 1.4;
    page-break-inside: auto;
}
thead {
    display: table-header-group;
}
tr {
    page-break-inside: avoid;
}
th {
    background-color: #1e3a5f;
    color: #ffffff;
    font-weight: 600;
    text-align: left;
    padding: 7pt 8pt;
    border: 0.5pt solid #1e3a5f;
}
td {
    padding: 6pt 8pt;
    border: 0.5pt solid #cbd5e1;
    vertical-align: top;
}
tr:nth-child(even) td {
    background-color: #f8fafc;
}
tr:hover td {
    background-color: #eff6ff;
}

/* Star ratings in tables */
td:first-child {
    font-weight: 500;
}

/* ── Images / Illustrations ── */
img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 14pt auto;
    border: 0.5pt solid #e2e8f0;
    border-radius: 4pt;
    box-shadow: 0 1pt 3pt rgba(0,0,0,0.08);
}
/* Figure captions (italic paragraphs after images) */
img + br + em,
p > em:only-child {
    display: block;
    text-align: center;
    font-size: 9.5pt;
    color: #64748b;
    margin-top: -8pt;
    margin-bottom: 14pt;
}

/* ── Lists ── */
ul, ol {
    margin-top: 4pt;
    margin-bottom: 10pt;
    padding-left: 22pt;
}
li {
    margin-bottom: 3pt;
}
li > ul, li > ol {
    margin-top: 2pt;
    margin-bottom: 2pt;
}

/* ── Code ── */
code {
    font-family: "SF Mono", "Fira Code", "Consolas", monospace;
    font-size: 9pt;
    background-color: #f1f5f9;
    padding: 1pt 4pt;
    border-radius: 3pt;
    color: #be185d;
}
pre {
    background-color: #1e293b;
    color: #e2e8f0;
    padding: 12pt 14pt;
    border-radius: 6pt;
    font-size: 8.5pt;
    line-height: 1.45;
    overflow-x: auto;
    margin: 10pt 0 14pt 0;
    page-break-inside: avoid;
}
pre code {
    background: none;
    padding: 0;
    color: inherit;
    font-size: inherit;
}

/* ── Blockquotes ── */
blockquote {
    border-left: 3pt solid #2563eb;
    margin: 10pt 0;
    padding: 8pt 14pt;
    background-color: #eff6ff;
    color: #1e40af;
    font-style: italic;
}
blockquote p {
    margin-bottom: 4pt;
}

/* ── Links ── */
a {
    color: #2563eb;
    text-decoration: none;
}

/* ── Strong/Em ── */
strong {
    font-weight: 600;
}

/* ── Sources section ── */
h2:last-of-type ~ ol {
    font-size: 9pt;
    color: #475569;
}
h2:last-of-type ~ ol a {
    word-break: break-all;
}

/* ── Page breaks before major sections ── */
h2 {
    page-break-before: auto;
}
/* Force page break before key sections */
h2:nth-of-type(n+3) {
    page-break-before: always;
}

/* ── Cover page ── */
.cover-page {
    text-align: center;
    page-break-after: always;
    padding-top: 15mm;
}
.cover-spacer {
    height: 5mm;
}
.cover-title {
    font-size: 28pt;
    font-weight: 700;
    color: #111;
    border-bottom: none;
    margin-bottom: 16pt;
    line-height: 1.3;
}
.cover-img {
    max-width: 75%;
    margin: 12pt auto;
    border: none;
    border-radius: 8pt;
}
.cover-subtitle {
    font-size: 14pt;
    color: #475569;
    margin-top: 16pt;
    margin-bottom: 24pt;
}
.cover-author {
    font-size: 16pt;
    font-weight: 600;
    color: #1a1a1a;
    margin-top: 24pt;
}
.cover-spacer-bottom {
    height: 15mm;
}
.cover-publisher {
    font-size: 12pt;
    font-style: italic;
    color: #64748b;
    margin-bottom: 4pt;
}
.cover-year {
    font-size: 12pt;
    color: #64748b;
}

/* ── Auto-generated ToC ── */
.toc {
    page-break-after: always;
}
.toc ul {
    list-style: none;
    padding-left: 0;
}
.toc > ul > li {
    margin-bottom: 6pt;
    font-weight: 600;
    font-size: 11pt;
}
.toc > ul > li > ul {
    padding-left: 18pt;
    margin-top: 3pt;
}
.toc > ul > li > ul > li {
    font-weight: 400;
    font-size: 10pt;
    margin-bottom: 2pt;
    color: #475569;
}
.toc a {
    color: #1e3a5f;
    text-decoration: none;
}
"""


def convert_md_to_pdf(md_path: str, pdf_path: str) -> None:
    """Convert a Markdown file to a styled PDF."""
    
    # Read markdown
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()
    
    # Strip YAML front matter if present
    if md_text.startswith("---"):
        end = md_text.find("---", 3)
        if end != -1:
            md_text = md_text[end + 3:].lstrip("\n")
    
    # Resolve relative image paths to absolute
    md_dir = os.path.dirname(os.path.abspath(md_path))
    def resolve_img(match):
        alt = match.group(1)
        src = match.group(2)
        if not os.path.isabs(src) and not src.startswith(("http://", "https://")):
            abs_src = os.path.join(md_dir, src)
            if os.path.exists(abs_src):
                src = "file://" + abs_src
        elif os.path.isabs(src):
            src = "file://" + src
        return f"![{alt}]({src})"
    
    md_text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", resolve_img, md_text)
    
    # Convert to HTML
    extensions = [
        "tables",
        "fenced_code",
        "codehilite",
        "toc",
        "smarty",
        "sane_lists",
    ]
    extension_configs = {
        "toc": {
            "permalink": False,
            "toc_depth": "2-3",
        },
    }
    html_body = markdown.markdown(md_text, extensions=extensions, extension_configs=extension_configs)
    
    # Wrap in full HTML
    html_doc = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <style>{CSS}</style>
</head>
<body>
{html_body}
</body>
</html>"""
    
    # Convert to PDF
    HTML(string=html_doc, base_url=md_dir).write_pdf(pdf_path)
    
    size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
    logger.info("PDF created: %s (%.1f MB)", pdf_path, size_mb)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    if len(sys.argv) < 2:
        logger.error("Usage: python md_to_pdf.py <input.md> [output.pdf]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    if not os.path.exists(input_file):
        logger.error("File not found: %s", input_file)
        sys.exit(1)
    
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        output_file = os.path.splitext(input_file)[0] + ".pdf"
    
    convert_md_to_pdf(input_file, output_file)
