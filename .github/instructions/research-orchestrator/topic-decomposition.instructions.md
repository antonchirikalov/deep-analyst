---
description: Rules for decomposing user topics into subtopics with priority assignment and document type detection.
---

# Topic Decomposition

## Document Type Detection

Parse the user query to determine document type:

| Type | Signal Words | Example |
|------|-------------|---------|
| **Comparative Analysis** | "compare", "vs", "versus", "difference between", "which is better" | "Compare React vs Vue vs Svelte" |
| **Technology Overview** | "what is", "overview", "explain", "how does X work" | "Overview of WebAssembly" |
| **State of the Art** | "SotA", "state of the art", "current state", "latest in" | "Current state of RAG systems" |
| **Research Report** | "impact of", "analysis of", "study", "investigate" | "Impact of quantization on inference" |

If ambiguous, default to **Comparative Analysis** (if multiple subjects) or **Technology Overview** (if single subject).

## Subtopic Decomposition

Break the topic into 3–6 subtopics. Each subtopic should be:
- **Focused** — answerable by a single Scout in one research session
- **Non-overlapping** — minimal duplication between subtopics
- **Balanced** — roughly equal scope

### Decomposition by Document Type

**Comparative Analysis:**
1. Overview of each participant (one subtopic per technology/approach)
2. Comparison criteria and methodology
3. Benchmarks and performance data
4. Use cases and adoption

**Technology Overview:**
1. Core concepts and architecture
2. How it works (internals)
3. Current implementations and ecosystem
4. Practical applications and limitations

**State of the Art:**
1. Historical evolution of approaches
2. Current leading methods (one subtopic per major method)
3. Benchmarks and evaluation metrics
4. Open problems and future directions

**Research Report:**
1. Problem definition and context
2. Existing approaches (literature review)
3. Each approach in depth (one subtopic per approach)
4. Results, data, and evaluation

## Priority Assignment

Assign priority to each subtopic based on importance:

| Priority | When to Use | Scout Behavior |
|----------|------------|----------------|
| `high` | Core topic, key differentiator, user's main interest | Full budget, all search tiers |
| `normal` | Supporting information, context, secondary aspects | Standard budget, tiers 1–2 |
| `quick` | Background, well-known facts, quick definitions | Minimal budget, tier 1 only |

**Rules:**
- At least one subtopic must be `high` priority
- No more than half of subtopics should be `quick`
- For `deep` search depth: all subtopics get `high`
- For `quick` search depth: all subtopics get `quick`
- For `normal` search depth: mix of `high` and `normal`

## Output Format

Pass to each Scout as task description:
```
Research subtopic: "[subtopic description]"
Priority: [high/normal/quick]
Output file: generated_docs_[TIMESTAMP]/research/[subtopic_slug].md
```
