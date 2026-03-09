---
description: "URL discovery strategy for the Retriever agent — search queries, quality filters, broadening rules."
---

# Link Discovery

## Search Strategy

### Primary search

Use `tavily_search` with a focused query matching the subtopic. Target 5-10 high-quality URLs.

### Query construction

1. Start with the subtopic name as the base query
2. Add qualifying terms that target IMPLEMENTATION details: "architecture", "internals", "source code", "API specification", "protocol", "implementation"
3. For code-related topics: include "github.com" and language-specific terms
4. For protocol/format topics: include "specification", "schema", "format", "RFC"
5. AVOID generic terms like "guide", "tutorial", "overview" — these find surface-level marketing content

### Source quality ranking

Prefer sources in this order:

| Priority | Source type | Example |
|---|---|---|
| 1 | GitHub source code and READMEs | github.com/org/repo (actual code, not just README) |
| 2 | Official API documentation | docs.github.com, docs.anthropic.com |
| 3 | Engineering blog posts WITH code examples | blog.anthropic.com, github.blog/engineering |
| 4 | Peer-reviewed papers / arXiv | arxiv.org/abs/... |
| 5 | Quality technical blogs WITH code | simonwillison.net, lilianweng.github.io |
| 6 | Official blog posts (no code) | blog.anthropic.com announcements |

### Sources to avoid

- Stack Overflow / Reddit (unless they contain unique technical data)
- Generic news aggregators (The Verge, TechCrunch — news announcements, not implementation details)
- SEO-optimized listicles ("Top 10 AI tools", "Best coding assistants")
- Marketing comparison pages without technical substance (SitePoint, Builder.io product comparisons)
- Paywalled content (Extractor will fail on these anyway)
- Content older than 2 years (for fast-moving tech topics)
- **Medium/Substack posts that just rephrase press releases** — they add no original technical content

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
