---
description: Source quality criteria and validation rules for Scout research output.
---

# Source Quality

## Source Authority Hierarchy

| Tier | Source Type | Trust Level | Examples |
|------|-----------|------------|---------|
| **S** | Official documentation | Highest | docs.python.org, react.dev, pytorch.org |
| **A** | Peer-reviewed papers | High | arXiv (with citations), ACL, NeurIPS |
| **B** | Vendor/project docs | High | AWS docs, GitHub README, HuggingFace model cards |
| **C** | Reputable tech blogs | Medium | Engineering blogs from major companies |
| **D** | Community discussion | Low | Stack Overflow, Reddit, HN |
| **E** | Personal blogs | Lowest | Medium posts, personal sites |

## Rules

1. **Minimum 60% from Tier S–B sources** — majority of facts should come from authoritative sources
2. **Never cite only Tier D–E** — if only community/blog sources found, flag to Orchestrator that source quality is low
3. **Cross-reference claims** — if a surprising fact comes from Tier C–E, verify with a Tier S–B source
4. **Freshness matters** — for technology topics, prefer sources from the last 2 years
5. **Include publication dates** — when available, note the date alongside the URL

## URL Validation

- Include full URLs, not shortened links
- Verify URLs are from known domains when possible
- If a URL returns 404 during extract, note it and find an alternative
- For papers: include arXiv ID or DOI when available

## What NOT to Source

- ❌ AI-generated content farms (aggregator sites with thin content)
- ❌ Outdated documentation (>3 years for fast-moving tech)
- ❌ Sources behind paywalls (unless content was accessible)
- ❌ Sources without clear authorship for controversial claims
- ❌ Marketing materials disguised as technical content
