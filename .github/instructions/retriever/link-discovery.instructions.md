---
description: "URL discovery strategy for the Retriever agent — search queries, quality filters, broadening rules."
---

# Link Discovery

## Search Strategy

### Primary search

Use `tavily_search` with a focused query matching the subtopic. Target 5-10 high-quality URLs.

### Query construction

1. Start with the subtopic name as the base query
2. Add qualifying terms for specificity: "architecture", "documentation", "benchmark", "comparison"
3. For technical topics, add terms like "official docs", "GitHub", "paper"

### Source quality ranking

Prefer sources in this order:

| Priority | Source type | Example |
|---|---|---|
| 1 | Official documentation | docs.github.com, docs.anthropic.com |
| 2 | Peer-reviewed papers / arXiv | arxiv.org/abs/... |
| 3 | Official blog posts | blog.anthropic.com, github.blog |
| 4 | GitHub repositories | github.com/org/repo (README, docs/) |
| 5 | Established tech publications | The Verge (tech), Ars Technica, InfoQ |
| 6 | Quality blog posts | simonwillison.net, lilianweng.github.io |

### Sources to avoid

- Stack Overflow / Reddit (unless they contain unique technical data)
- Generic news aggregators
- SEO-optimized listicles
- Paywalled content (Extractor will fail on these anyway)
- Content older than 2 years (for fast-moving tech topics)

## Broadening Rules

If initial search returns <3 URLs:

### Attempt 1: Synonym expansion
- Replace jargon with common terms
- Add alternative product/project names
- Try broader category: "AI coding tools" instead of "Codex CLI"

### Attempt 2: Remove constraints
- Drop date restrictions
- Drop specificity qualifiers
- Search for the parent category

### After 2 attempts
- Write whatever URLs you found (even 1-2)
- The Analyst will mark this subtopic as SHALLOW/INSUFFICIENT
- The Planner will merge it with a stronger neighbor

## Output Validation

Before writing `_links.md`, verify:
- Each URL is unique (no duplicates)
- Each URL starts with `http://` or `https://`
- Brief description is present for each URL
- URLs are numbered sequentially starting from 1
- **EACH source is exactly ONE line:** `N. https://url — description`
- **NO multi-line entries** (no `- URL:` sub-items, no bold titles on separate lines)
