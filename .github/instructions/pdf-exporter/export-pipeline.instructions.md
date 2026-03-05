````instructions
---
description: PDF export pipeline — pre-processing, conversion, and verification steps for Markdown-to-PDF conversion with images and tables.
---

# Export Pipeline

## Overview

Convert a finalized Markdown research document into a publication-quality PDF that correctly renders:
- Embedded PNG illustrations (absolute paths)
- Markdown tables with alignment
- Headings hierarchy (H1–H3)
- Bold/italic/links
- Bulleted and numbered lists

## Step 1: Locate Source Document

Find the document to convert:

```
Priority order:
1. User-specified file path
2. FINAL_REPORT.md in the latest generated_docs_* folder
3. Latest draft/vN.md (highest N) in the latest generated_docs_* folder
```

Also locate the `illustrations/` folder relative to the document.

## Step 2: Convert to PDF

Run the conversion script from the workspace root:

```bash
.venv/bin/python .github/skills/pdf-exporter/scripts/md_to_pdf.py <input.md> [output.pdf]
```

The script (`md_to_pdf.py`) handles everything automatically:
- Strips YAML front matter if present
- Resolves relative image paths to absolute `file://` URIs
- Validates image file existence
- Converts Markdown → HTML using `markdown` library (tables, fenced_code, toc, smarty, sane_lists)
- Applies publication-quality CSS styling (A4, colored headings, zebra-striped tables, image borders, pagination, page numbers)
- Renders HTML → PDF via `weasyprint`

No temporary files or manual pre-processing needed.

Output file naming:
- If source is `FINAL_REPORT.md` → `FINAL_REPORT.pdf`
- If source is `draft/v3.md` → `draft/v3.pdf`
- If no output path given, defaults to same name with `.pdf` extension
- Always save in the same directory as the source

## Step 3: Verify Output

1. Confirm the PDF file was created (the script prints ✅ on success)
2. Report file size (printed by the script)

## Error Handling

| Error | Action |
|-------|--------|
| `weasyprint` not installed | Run: `pip install weasyprint markdown` |
| `markdown` not installed | Run: `pip install markdown` |
| Images not rendering | Check relative paths resolve correctly from the .md file's directory |
| Tables broken in PDF | Simplify complex tables (remove merged cells, reduce columns) |
| Script not found | Path: `.github/skills/pdf-exporter/scripts/md_to_pdf.py` |

## Usage Examples

User says:
- "Сконвертируй отчёт в PDF" → find latest FINAL_REPORT.md, convert
- "PDF из draft/v2.md" → convert that specific file
- "Экспортируй в PDF папку generated_docs_20260305_195733" → find FINAL_REPORT.md there

````
