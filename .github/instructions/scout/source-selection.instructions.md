---
description: Source priority rules for Scout — when to use Context7, GitHub, HuggingFace, Tavily, and other tools based on subtopic type.
---

# Source Selection Priority

Before diving into web search, pick the fastest authoritative source.

## Priority Table

| Priority | Source | When to Use | Speed |
|----------|--------|------------|-------|
| 1 | **Context7** (`mcp_context7_*`) | Subtopic is about a specific library/framework (React, PyTorch, LangChain, etc.) | ⚡ Instant — returns official docs directly |
| 2 | **GitHub** (`mcp_github_*`) | Researching open-source projects — repo stats, README, code search, releases | ⚡ Fast — structured API |
| 3 | **HuggingFace** (`mcp_huggingface_*`) | Scientific papers, ML models, datasets | ⚡ Fast — structured API |
| 4 | **Tavily** (`mcp_tavily-remote_*`) | General web search, news, blog posts, comparisons | 🐢 Slower — web crawling |
| 5 | **PDF reader** (`mcp_pdf-reader_*`) | Reading specific PDF documents (whitepapers, reports) | Depends on file size |

## Decision Rules

- If the subtopic **names a specific library** → Context7 first
- If it's about an **open-source project** → GitHub first (search repos, read README)
- If it's **academic or ML-related** → HuggingFace first (paper search)
- If none of the above → Tavily search (basic tier first)
- **PDF reader** only when a specific PDF URL/file is known

## Combining Sources

For complex subtopics, you may need 2–3 sources:
- Context7 for API docs + Tavily for community discussion
- GitHub for code examples + HuggingFace for paper backing
- Tavily for overview + PDF reader for a specific whitepaper

Always start with the fastest authoritative source, then supplement with others only if needed.

## Anti-Patterns

- ❌ Searching Tavily for React docs when Context7 has them
- ❌ Using Tavily to find a GitHub repo README (use GitHub MCP directly)
- ❌ Running multiple tools for the same information
- ❌ Skipping Context7/GitHub/HF and going straight to Tavily
