---
description: Overall search approach, tool selection strategy, and research process for Scout agent.
---

# Search Strategy

## Research Process

1. **Receive assignment** — subtopic, priority level, output file path
2. **Assess topic type** — library/framework? OSS project? academic? general?
3. **Choose primary source** — based on topic type (see Source Selection)
4. **Execute tiered search** — basic first, deepen only if insufficient
5. **Structure findings** — facts, data points, quotes, sources
6. **Write output file** — structured markdown to specified path

## Source Selection Decision Tree

```
Is the subtopic about a specific library/framework?
  YES → Context7 first (mcp_context7_resolve_library_id + mcp_context7_get_library_docs)
  NO ↓

Is it about an open-source project?
  YES → GitHub first (search_repositories, get_file_contents for README)
  NO ↓

Is it academic/scientific?
  YES → HuggingFace first (paper_search, model_search)
  NO ↓

General topic → Tavily search (basic first)
```

## Tool Usage Rules

| Tool | Primary Use | When NOT to Use |
|------|-----------|-----------------|
| **Context7** | Library/framework docs (React, PyTorch, etc.) | General topics without a specific library |
| **GitHub** | OSS repos, code examples, project stats | Non-software topics |
| **HuggingFace** | Papers, models, datasets, ML-specific | Non-ML/AI topics |
| **Tavily search** | General web search, news, blog posts | When Context7/GitHub/HF already answered |
| **Tavily extract** | Deep content from specific URLs | Don't use "just in case" — only for valuable URLs |
| **Tavily research** | Deep synthesis on complex topics | Quick/normal priority subtopics |
| **PDF reader** | Reading specific PDF files | When web sources suffice |
| **fetch_webpage** | Direct URL access | When Tavily extract works |

## No-Duplication Rule

DO NOT search the same thing with different tools. If `tavily_search` found comprehensive information on a topic, don't run `tavily_research` on the same topic. If Context7 provided library docs, don't additionally search Tavily for the same information.

## Early Exit Rule

If you have 5+ relevant facts with sources after initial searches — **stop searching**. Don't burn budget on marginal additional data. Quality over quantity.

## Research Quality Checklist

Before writing the output file, verify:
- [ ] At least 5 key facts with source attribution
- [ ] At least 3 different source URLs
- [ ] Numerical data/benchmarks included (if available)
- [ ] No unsourced claims
- [ ] Facts are structured and non-overlapping
