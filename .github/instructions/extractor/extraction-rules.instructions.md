---
description: "Deep content extraction rules for the Extractor agent — extraction tools, fallback chain, error handling, output format."
---

# Extraction Rules

## Extraction Chain

For each URL in `_links.md`, try extraction tools in order:

### 1. `tavily_extract` (primary)

```
tavily_extract(url, mode="basic")
```

- Best for: articles, blog posts, documentation pages
- Returns: structured text content
- If fails (403, timeout, empty): try next tool

For protected or complex pages:
```
tavily_extract(url, mode="advanced")
```

### 2. `fetch_webpage` (fallback)

- Best for: simple HTML pages, GitHub READMEs
- Returns: raw HTML → you must extract meaningful text
- If fails: skip this URL

### 3. Skip and log

If both tools fail → log the error and move to the next URL.

```bash
python3 .github/skills/workflow-logger/scripts/agent-trace.py log \
  --folder $BASE_FOLDER --agent Extractor --phase 2 \
  --action extract --status fail \
  --target "{url}" --detail "{error reason}"
```

## Content Processing

After extracting raw content:

1. **Structure with Markdown headings** — add H2/H3 headers for navigation, preserving the source's logical sections
2. **COPY code examples verbatim** — preserve in fenced code blocks with language tags. NEVER omit code.
3. **COPY data tables verbatim** — preserve in Markdown table format
4. **Remove ONLY boilerplate** — navigation menus, footers, ads, cookie banners, sidebars
5. **NEVER paraphrase technical content** — copy the source's explanations, not your summary of them
6. **COPY ALL low-level details verbatim** — file formats, JSON schemas, directory structures, API payloads, config examples, protocol specs, CLI commands, environment variables
7. **COPY numbers and metrics verbatim** — benchmarks, pricing, token limits, latency measurements

### ANTI-SUMMARIZATION CHECK

Before writing each extract, compare:
- Input content from tavily/fetch: ~N words
- Your extract output: ~M words
- If M < N × 0.5 → **YOU ARE SUMMARIZING. GO BACK AND COPY MORE CONTENT.**
- Acceptable ratio: M ≥ N × 0.6 (you can trim boilerplate but not technical content)

## Extract File Format

```markdown
# Extract: {page title or descriptive name}
Source: {full URL}
Words: ~{count}

## {Section heading from content}

{content}

## {Another heading}

{more content}
```

### Sizing guidelines

| Content length | Action |
|---|---|
| <500 words | Short content — write as-is, may be thin |
| 500-4000 words | Ideal range — full extraction |
| 4000+ words | Extract most relevant portions, prioritize technical depth |

**MINIMUM TARGET: 1500 words per extract.** A 600-word extract from a 3000-word source means you are summarizing instead of extracting. Copy the source content with its original structure, examples, code blocks, and technical details. Only remove navigation/ads/boilerplate.

## URL Parsing

Parse URLs from `_links.md` using flexible matching:
- **Primary:** Lines matching `^\d+\.\s+https?://` (e.g., `1. https://example.com — description`)
- **Fallback:** Any line containing `https://` (handles `- URL: https://...`, bold titles with inline URLs, etc.)
- Deduplicate URLs before processing
- **Process ALL URLs** — do NOT stop after the first one

## Extract Numbering

Before writing the first extract:
1. Check existing `extract_*.md` files in the subtopic folder via `list_dir`
2. Find the highest existing number N
3. Start your extracts from N+1

This prevents collisions if the Extractor is re-run after a partial failure.

## Chunked Writing

Extracts may exceed the output token limit. If content is >3000 words:

1. Create the file with the first ~3000 words, ending with:
   ```
   <!-- SECTION_CONTINUES -->
   ```
2. Use `replace_string_in_file` to replace the marker with the next chunk
3. Repeat until all content is written

## Error Handling

| Error | Action |
|---|---|
| 403 Forbidden | Skip URL, log warning — likely paywalled |
| 404 Not Found | Skip URL, log warning — dead link |
| Timeout (>30s) | Skip URL, log warning |
| Empty content | Skip URL, log warning — page may require JS |
| Encoding errors | Try to extract what's readable, skip garbled sections |

If ALL URLs fail for a subtopic, write a minimal extract file noting the failure:
```markdown
# Extract: Extraction Failed
Source: N/A
Words: ~50

All URLs in _links.md returned errors. This subtopic has no usable content.
Analyst should mark this as INSUFFICIENT.
```
