---
description: "Deep search strategy for the Researcher agent — multi-query search, source evaluation, extraction depth, fallback cascade."
---

# Deep Search Strategy

## Search Query Construction

For each subtopic, use **multiple search channels**:

### Web queries (Tavily)
1. **Primary:** `"{subtopic} technical deep dive documentation"` — finds official docs and detailed guides
2. **Alternate:** `"{subtopic} guide tutorial overview"` — broader search for tutorials
3. **Code-focused:** `"{subtopic} github source code architecture"` — finds repos and code walkthroughs

### GitHub queries (for OSS topics)
- `mcp_github_search_repositories(query="{tool name}")` — find canonical repos
- `mcp_github_search_code(query="{architecture keyword}")` — find implementation files
- Then read key files with `mcp_github_get_file_contents(owner, repo, path)` — README.md, docs/, architecture files

### HuggingFace queries (for ML/AI topics)
- `mcp_huggingface_paper_search(query="{research topic}")` — find arXiv papers
- `mcp_huggingface_hf_doc_search(query="{library or concept}")` — search HF library docs
- `mcp_huggingface_hub_repo_search(query="{model name}")` — find model cards with technical specs

### Confluence queries (only when specified in prompt)
- `mcp_mcp-atlassian_confluence_search(query="{topic}")` — search internal wiki
- `mcp_mcp-atlassian_confluence_get_page(page_id)` — read specific pages

### Query Tips
- Include the overall research topic for context: `"KV cache optimization for LLM inference"`
- Use domain-specific terms, not generic phrases
- For comparisons: search each item separately, then comparison articles
- Use GitHub for ground-truth source code reading — it's the most reliable source for OSS

## Source Evaluation

Before extracting, evaluate source quality:

| Priority | Source type | How to get it |
|----------|-----------|---|
| 1 | GitHub repos (README, architecture docs, source) | `github_search_repositories` → `github_get_file_contents` |
| 2 | Official documentation | Tavily search → `tavily_extract` / `fetch_webpage` |
| 3 | Papers (arXiv, proceedings) | `hf_paper_search` → `fetch_webpage` |
| 4 | HuggingFace model cards & docs | `hf_doc_search` / `hub_repo_search` |
| 5 | Engineering blog posts (Meta, Google, Anthropic) | Tavily → `tavily_extract` / `fetch_webpage` |
| 6 | Confluence internal wiki | `confluence_search` → `confluence_get_page` |
| 7 | General tech articles | Tavily → `fetch_webpage` |

**Skip:** paywalled articles, SEO spam, aggregator sites with no original content.

## Extraction Depth

The extraction phase is the **most critical** part of the pipeline. All downstream phases (Analysis, Writing) depend on extract quality.

### What "verbatim" means
- Copy the article's full text, not a summary
- Keep all code blocks with original formatting
- Keep all JSON/YAML examples, CLI commands, file paths
- Keep tables, numbered lists, structured data
- If the article has 3000 words, your extract should have ~3000 words

### What to skip in extracts
- Navigation menus, footer links, cookie banners
- "Related articles" sections
- Social media share buttons markup
- Advertising content

## Fallback Cascade

When primary tools fail, fall back through the chain:

**Search fallback:**
```
tavily_search → tavily_search(alt query) → github_search → hf_paper_search → own knowledge (list known URLs)
```

**Extraction fallback:**
```
tavily_extract → fetch_webpage → skip URL
github_get_file_contents → skip (no fallback needed, direct API)
confluence_get_page → skip
```

If Tavily returns 432 (rate limit exceeded), switch immediately to `fetch_webpage` for ALL remaining web URLs — don't retry Tavily. GitHub and HuggingFace MCP tools are independent of Tavily and should still work.

## File Naming

- Links: `{subtopic_folder}/_links.md`
- Extracts: `{subtopic_folder}/extract_1.md`, `extract_2.md`, ... (numbered by URL order in _links.md)
