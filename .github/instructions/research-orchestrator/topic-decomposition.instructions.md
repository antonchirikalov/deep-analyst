---
description: "Phase 0 topic decomposition rules — parsing user request into parameters and subtopics for parallel research."
---

# Topic Decomposition

## Overview

Phase 0 is the Orchestrator's only "intelligent" task. Everything after is mechanical scheduling. Quality of decomposition directly impacts research quality.

## Parameter Parsing

Extract from the user's request:

### Document size (max_pages)

| User signal | Size tier | max_pages |
|---|---|---|
| "краткий", "brief", "overview", "summary" | Brief | 5-8 |
| "стандарт", "отчёт", "report" (or no indication) | Standard | 15-20 |
| "подробный", "detailed", "comprehensive", "in-depth" | Detailed | 25-30 |
| Explicit number ("20 страниц", "15 pages") | Custom | as specified |

Default if ambiguous: **20 pages** (standard).

### Language detection

Detect from the user's prompt language:
- "Напиши отчёт о..." → `language: Russian`
- "Write a report on..." → `language: English`
- Mixed language → use the language of the main request body

### Audience and tone

Infer from context:
- Academic/research context → `audience: technical`, `tone: academic`
- Business/executive context → `audience: executive`, `tone: business`
- General/educational → `audience: general`, `tone: conversational`

Default: `audience: technical`, `tone: academic`.

### Formulas policy

Default: `formulas: avoid — only essential formulas, always preceded by 2+ paragraphs of conceptual explanation. Never start a subsection with a formula.`

Override only if user explicitly requests math-heavy content.

## Subtopic Decomposition

Break the main topic into **7-12 subtopics** for parallel research. More subtopics = deeper coverage. For "detailed" documents, prefer 10-12 subtopics.

### Decomposition principles

1. **Orthogonal coverage** — subtopics should cover different aspects, not overlap significantly
2. **Searchable terms** — each subtopic should yield good search results (use common terms, not jargon)
3. **Balanced scope** — each subtopic should produce roughly similar amount of material
4. **Research-oriented** — subtopics are search directions, NOT document sections (Planner reorganizes later)
5. **Granularity over breadth** — prefer splitting a broad area into 2-3 focused subtopics rather than one giant one. E.g., instead of "optimization techniques" → split into "quantization methods", "attention optimization", "batching and scheduling"

### Subtopic naming

Use lowercase slug format for folder names:
- "Architecture and Design Patterns" → `architecture_design_patterns`
- "Сравнение производительности" → `performance_comparison`
- Keep slugs short (2-4 words), no special characters

### Examples

**Topic:** "AI coding assistants comparison: Copilot, Claude Code, Codex CLI"

Subtopics:
1. `github_copilot_agent` — GitHub Copilot agent architecture, workspace mode, coding features
2. `claude_code` — Claude Code architecture, agentic workflow, multi-file editing
3. `openai_codex_cli` — Codex CLI architecture, sandbox model, local execution
4. `security_sandboxing` — Security models comparison, sandboxing approaches, permission systems
5. `mcp_integrations` — Model Context Protocol support, tool ecosystem, extensibility
6. `benchmarks_pricing` — Performance benchmarks, pricing models, token usage comparison

**Topic:** "Transformer architecture deep dive"

Subtopics:
1. `self_attention_mechanism` — Multi-head self-attention, QKV, computational complexity
2. `positional_encoding` — Sinusoidal, learned, RoPE, ALiBi approaches
3. `training_optimization` — Learning rate schedules, gradient accumulation, mixed precision
4. `architecture_variants` — GPT, BERT, T5, encoder-decoder vs decoder-only
5. `scaling_laws` — Chinchilla, Kaplan, compute-optimal training
6. `inference_optimization` — KV cache, speculative decoding, quantization

## Output

Write `research/_plan/params.md` with the structure shown in the agent file.

The subtopic list in params.md drives the parallelism: one Researcher per subtopic (Phase 1), one Analyst per subtopic (Phase 2).
