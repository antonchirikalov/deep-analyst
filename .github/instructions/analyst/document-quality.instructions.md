---
description: Document quality criteria for Analyst — structure, language, forbidden elements, and required elements for publication-quality analytical documents.
---

# Document Quality Criteria

The analytical document is a **product for human reading**, not a technical dump.

## Structure and Readability

| Criterion | Requirement |
|-----------|------------|
| **Clear hierarchy** | Headings H1→H2→H3 logically nested. Reader understands structure from table of contents |
| **Paragraphs of 3–5 sentences** | No "walls of text". One paragraph = one idea |
| **Section transitions** | Each section starts with context: what it covers and why |
| **Executive Summary** | First section — 5–7 sentence summary with key conclusions |

## Language and Style

| Criterion | Requirement |
|-----------|------------|
| **Clear language** | Write for a senior engineer, not for a PhD. Explain terms on first use |
| **No jargon for jargon's sake** | If it can be said more simply — say it more simply |
| **Active voice** | "LoRA reduces memory consumption", not "Memory consumption is reduced when using LoRA" |
| **Specifics over vague language** | "reduces by 40%" instead of "significantly reduces" |

## What Must NOT Be in the Document

| Forbidden | Why |
|-----------|-----|
| ❌ Code blocks (>5 lines) | This is an analytical document, not a tutorial. Max 1–2 inline lines for syntax illustration |
| ❌ Configuration examples | Don't overload reader with YAML/JSON. If needed — link to documentation |
| ❌ Step-by-step instructions | This is not a how-to guide. Describe the principle, not the procedure |
| ❌ Copy-paste from sources | Rephrase + cite. Quotes — only short and meaningful ones |
| ❌ Listing all API parameters | Only key parameters that affect the choice |
| ❌ Repeating the same point | A fact is mentioned once in the appropriate section |

## Required Elements

| Element | Where |
|---------|-------|
| Executive Summary (5–7 sentences) | Beginning of document |
| Comparison table (if >2 approaches) | Before detailed comparison |
| Illustration placeholders (3–5) | Throughout text — `<!-- ILLUSTRATION: ... -->` for PaperBanana PNG generation |
| Bulleted conclusions | End of each comparison section |
| Final recommendation with rationale | Final section |
| Sources with brief descriptions | End of document |

## Size Guidelines

The Orchestrator may pass a `max_pages` constraint from the user. If provided, it takes precedence over the defaults below.

| Document Type | Default Page Count |
|--------------|-------------------|
| Comparative Analysis | 8–12 |
| Technology Overview | 6–10 |
| State of the Art | 8–12 |
| Research Report | 6–10 |

When `max_pages` is specified, stay within ±10% of the target. Adjust depth, number of subsections, and diagram count proportionally.
