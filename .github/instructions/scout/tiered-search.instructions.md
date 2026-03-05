---
description: Tavily three-tier speed management strategy for optimizing Scout search performance and response time.
---

# Tiered Search (Tavily)

Tavily calls can be slow. Use a three-tiered strategy to optimize response time.

## Level 1 — Quick Scan (always first)

```
tavily_search:
  search_depth: "basic"
  max_results: 5
  topic: "general"
```

Goal: get a general picture of the subtopic in ~3–5 sec. If enough facts (5+) — **stop here**.

## Level 2 — Deep Search (when data is insufficient)

```
tavily_search:
  search_depth: "advanced"
  max_results: 10
  include_raw_content: true
```

Triggered only if Level 1 yielded < 3 significant facts or the topic is complex/niche.

## Level 3 — Deep Research (only for key subtopics)

```
tavily_research:
  model: "mini"
  max_results: 10
```

- Use `model: "mini"` for 80% of subtopics (faster, cheaper)
- Use `model: "pro"` only for broad/complex topics where mini produces insufficient synthesis
- Only used when Orchestrator marked subtopic as `priority: high`

## Tier Selection by Priority

| Priority | Tiers Allowed | Max tavily_search | tavily_research |
|----------|--------------|-------------------|-----------------|
| `quick` | Level 1 only | 2 | No |
| `normal` | Levels 1–2 | 3 | No |
| `high` | Levels 1–3 | 3 | 1 (mini or pro) |

## Optimization Rules

1. **Start with basic** — always `search_depth: "basic"` first
2. **Early exit** — if 5+ relevant facts with sources → do not go deeper
3. **extract only by URL** — `tavily_extract` only for specific URLs from results, not "just in case"
4. **extract_depth: basic** — use `advanced` only for protected sites / PDF-heavy pages
5. **mini > pro** — tavily_research with `model: "mini"` default
6. **No duplicates** — don't search the same thing at multiple tiers; escalate only if previous tier was insufficient
