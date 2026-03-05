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
| **Explain, don't transcribe** | Never copy a formula as the explanation. The TEXT is the explanation; the formula is an optional visual aid |
| **Active voice** | "LoRA reduces memory consumption", not "Memory consumption is reduced when using LoRA" |
| **Specifics over vague language** | "reduces by 40%" instead of "significantly reduces" |
| **Concrete examples** | "for a 512-token input, this means 262,144 comparisons" instead of "quadratic complexity O(n²)" |

## What Must NOT Be in the Document

| Forbidden | Why |
|-----------|-----|
| ❌ Code blocks (>5 lines) | This is an analytical document, not a tutorial. Max 1–2 inline lines for syntax illustration |
| ❌ Configuration examples | Don't overload reader with YAML/JSON. If needed — link to documentation |
| ❌ Step-by-step instructions | This is not a how-to guide. Describe the principle, not the procedure |
| ❌ Copy-paste from sources | Rephrase + cite. Quotes — only short and meaningful ones |
| ❌ Listing all API parameters | Only key parameters that affect the choice |
| ❌ Repeating the same point | A fact is mentioned once in the appropriate section |

## Technical Depth by Content Tier

The `content_depth` parameter (set by Orchestrator based on document size) controls formula and math density.

### Universal Principle (ALL TIERS)

**The document is written for humans, not for LaTeX compilers.** At every depth tier:
- The reader MUST understand the concept from the prose alone, without reading any formula
- A formula is NEVER the explanation — it is an optional supplement after the explanation
- If you remove every formula from the document, it must still make complete sense
- Prefer concrete examples ("for a sentence of 10 words, the model compares each word with all 10, so 100 comparisons") over abstract notation
- Use analogies and visual language liberally — they are not "dumbing down", they are good writing

### `conceptual` (brief documents)
- **ZERO formulas.** No LaTeX, no math notation, no Greek letters in equations
- Every technical concept explained with analogies, visual metaphors, or plain language
- Replace formulas with `<!-- ILLUSTRATION -->` placeholders for explanatory diagrams
- Tone: accessible, engaging, visual. "Imagine attention as a spotlight searching across words..."
- Use concrete examples and comparisons to everyday concepts
- **Test:** A product manager should understand every paragraph

### `balanced` (standard documents)
- **Max 2–3 key formulas** in the entire document (e.g., core attention equation, softmax)
- Every formula MUST be PRECEDED by a full plain-language explanation — not just followed
- The formula is a "for the curious" aside, not the main content
- Lead with intuition and concrete examples FIRST, then optionally show the formula
- Supplement formulas with visual `<!-- ILLUSTRATION -->` placeholders
- Tone: precise but not academic. "Here's the core idea, and for those interested, the math behind it..."
- **Test:** A senior engineer outside the domain should follow along comfortably without reading any formula

### `deep` (detailed documents)
- **Formulas allowed** where they add precision — but ALWAYS preceded by a clear explanation
- Include derivations, complexity analysis, mathematical proofs where relevant
- Every formula and derivation MUST start with "In plain terms, this means..." explanation BEFORE the math
- Notation tables at the start of technical sections
- Tone: rigorous AND readable. Full mathematical treatment, but never at the expense of clarity
- **Test:** An ML researcher should find the depth satisfying, AND a senior engineer should still follow the main ideas by reading only the prose

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
