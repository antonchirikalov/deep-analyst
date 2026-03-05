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

## Step 2: Pre-process Markdown

Create a temporary file `_export.md` in the same directory as the source.

### 2.1 Add PDF Metadata

If the document doesn't start with a YAML front matter block, prepend:

```yaml
---
title: "<extracted from first H1 heading>"
date: "<current date>"
---
```

### 2.2 Fix Image Paths

For every image reference in the document:

```markdown
# Before (relative)
![Architecture](illustrations/diagram_1.png)

# After (absolute)
![Architecture](/full/absolute/path/to/illustrations/diagram_1.png)
```

**Validation:** Check that each referenced image file actually exists. If missing, add a warning comment:
```markdown
<!-- WARNING: Image not found: illustrations/diagram_X.png -->
```

### 2.3 Verify Illustration References

All illustrations are PaperBanana PNGs in `illustrations/`. For each image reference:

1. Check that the referenced PNG file exists in `illustrations/`
2. If found → convert to absolute path for PDF rendering
3. If missing → add a warning placeholder:
   ```markdown
   > **[Illustration missing: diagram_N.png]** — Image file not found.
   ```
4. If any `<!-- ILLUSTRATION -->` placeholders remain unreplaced, warn about unprocessed illustrations

### 2.4 Validate Tables

For each Markdown table:
- Ensure the separator row exists (e.g., `|---|---|---|`)
- Ensure all rows have the same number of columns
- Trim excessive whitespace in cells

## Step 3: Convert to PDF

Call the MCP tool:

```
mcp_pdf-reader_markdown_to_pdf(
  markdown_file_path = "<path to _export.md>",
  pdf_file_path = "<output path>.pdf"
)
```

Output file naming:
- If source is `FINAL_REPORT.md` → `FINAL_REPORT.pdf`
- If source is `draft/v3.md` → `draft/v3.pdf`
- Always save in the same directory as the source

## Step 4: Verify Output

1. Confirm the PDF file was created
2. Report file size
3. If the tool supports page count, report that too

## Step 5: Clean Up

- Delete the temporary `_export.md` file
- Keep the original `.md` unchanged

## Error Handling

| Error | Action |
|-------|--------|
| MCP tool unavailable | Suggest: `pandoc <file>.md -o <file>.pdf --pdf-engine=wkhtmltopdf` |
| Images not rendering | Check if paths are absolute; suggest re-running with path fixes |
| Tables broken in PDF | Simplify complex tables (remove merged cells, reduce columns) |
| File too large for tool | Split document and convert in parts, then suggest manual merge |

## Usage Examples

User says:
- "Сконвертируй отчёт в PDF" → find latest FINAL_REPORT.md, convert
- "PDF из draft/v2.md" → convert that specific file
- "Экспортируй в PDF папку generated_docs_20260305_195733" → find FINAL_REPORT.md there

````
