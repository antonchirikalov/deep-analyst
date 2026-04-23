---
description: "Formalized verdict format for the Critic agent — review structure, severity levels, verdict guidelines, per-section feedback."
---

# Verdict Format

## Review Structure

Every review follows this exact format in `draft/_review.md`:

```markdown
## Verdict: APPROVED | REVISE | REJECTED

## Sections to revise
- section: {NN}_{slug}.md | severity: HIGH | issue: {specific, actionable description}
- section: {NN}_{slug}.md | severity: MEDIUM | issue: {specific, actionable description}

## Sections OK: {comma-separated section numbers}

## Overall notes
{Free-form feedback — what works well, general observations, suggestions}
```

### Format rules

- `## Verdict:` header MUST be in **English**, even if the document is in another language
- Section filenames reference the files in `draft/_sections/`
- Each issue line follows the exact pipe-delimited format shown above
- "Sections OK" lists section NUMBERS only (e.g., `01, 03, 04, 06`)

## Verdict Decision Matrix

| Verdict | When | Orchestrator action |
|---|---|---|
| **APPROVED** | All sections meet quality bar. Only LOW severity issues remain. | Proceed to Phase 7 (Illustration) |
| **REVISE** | 1+ sections have HIGH or MEDIUM severity issues | Re-run listed Writers + Editor + Critic (max 2 loops) |
| **REJECTED** | Fundamental structural problems; most sections need major rewrite | Treated as REVISE by Orchestrator, but with escalated logging |

### When to APPROVE

- Content is substantive — explains HOW things work, not just WHAT they are
- Includes technical details: code examples, JSON schemas, file paths, config formats, CLI commands
- Style matches params.md (audience, tone, language)
- Word counts are within ±15% of budget per section
- **Total word count ≥ 80% of target (max_pages × 300).** If target is 25 pages (7500 words) and document is 5500 words — this is NOT approvable.
- Minor issues only (formatting, small wording improvements)
- No significant filler or marketing language

### When to REVISE

- A section lacks depth (mentions concepts but doesn't explain HOW they work internally)
- **Missing technical details:** extracts contain JSON structures, file paths, protocol specs, API operation lists, but the section just summarizes them in 2 sentences. **Cross-check against the source extracts listed in toc.md — if ≥50% of technical artifacts are missing, this is HIGH severity.**
- Factual gaps: key aspects of the topic are missing
- **Filler content:** sentences like "Х использует мощный подход к Y" without explaining what the approach IS
- Style mismatch: wrong tone for the audience, or wrong language
- Word count: a section is >30% UNDER budget while source extracts contain unused material
- **Total document is <80% of target word count** (e.g., 5500 words for a 25-page target = REVISE)
- **Same content appears in multiple sections** (duplication instead of depth)
- Poor structure within a section (jumping between unrelated ideas)
- **Formulas without conceptual explanation:** a subsection starts with math/equations, or explains a concept in dry textbook language without vivid analogies and intuitive walkthroughs. The reader should understand WHY something exists and HOW it works from prose alone before seeing any formula. This is HIGH severity — the Writer must rewrite with concept-first structure, using Feynman-quality explanations.
- **Section under budget is NEVER an issue if all extract material is covered.** Over budget due to depth is FINE.

### When to REJECTED

- Most sections need fundamental rewriting
- Document structure doesn't match the ToC plan
- Content is largely off-topic or superficial

## Severity Levels

| Severity | Meaning | Triggers rewrite? |
|---|---|---|
| **HIGH** | Missing critical content, factual errors, fundamentally weak section | YES — Writer rewrites |
| **MEDIUM** | Insufficient depth, weak examples, style issues, minor structural problems | YES — Writer improves |
| **LOW** | Minor wording, formatting, could be slightly better but acceptable | NO — informational only |

Only list HIGH and MEDIUM severity items in the "Sections to revise" block. LOW severity items go in "Overall notes".

## What to IGNORE

Do NOT flag these as issues:
- `<!-- ILLUSTRATION: ... -->` placeholder comments — these are for the illustration phase (Phase 7)
- `![Рис. N]` image references that don't resolve yet — images are generated in Phase 7
- Minor formatting that the Editor handles (heading levels, spacing)

## Evaluation Criteria

### Content quality (most important)
- Are mechanisms explained with HOW-level depth? (not just "uses a mailbox" but "messages stored as JSON at ~/.claude/mailbox/{id}/inbox/, containing fields: sender, recipient, content, timestamp")
- Are there concrete examples, data points, or code snippets FROM THE SOURCE MATERIAL?
- Is the content accurate based on the source material?
- Does each section add **unique** value? (Same content in sections 3 and 8 = duplication)
- Is there filler/marketing language? ("мощный", "инновационный", "comprehensive", "революционный" without substance)

### Concept-before-formula (critical quality check)

This is the most common quality failure. Scan EVERY H3 subsection for this pattern:

- **For each H3 subsection:** does it open with 2-3 paragraphs that explain the concept so clearly and vividly that a reader could explain it to someone else in their own words — BEFORE any formula appears?
- **Quality bar for explanations:** The writing should feel like best-in-class technical communication — Feynman-lecture clarity, Karpathy-blog vividness, 3Blue1Brown narrative flow. The reader should think "now I get it" before ever seeing math. Dry, terse, textbook-style prose ("In the attention mechanism, for position $i$...") is NOT sufficient.
- **VIOLATION = HIGH severity:** A subsection that opens with a formula, math notation, or a sentence containing $...$ LaTeX before at least 2 paragraphs of plain-language explanation. Also HIGH: jumping straight to "how" (mechanism details) without first explaining "what" (the problem and the idea).
- **VIOLATION = MEDIUM severity:** A formula appears with only 1-2 sentences of context. Or the explanation exists but is too dry/terse — reads like a textbook definition rather than a vivid, intuitive walkthrough.
- **Litmus test:** Cover the formula with your hand. Can the reader still understand the concept from the surrounding text alone? If removing the formula leaves a gap in understanding → the prose explanation is insufficient.

### Extract coverage (second most important)
- Read the source extracts assigned to each section (listed in toc.md Sources field)
- Does the section include the key technical artifacts from those extracts?
- **If an extract contains a JSON schema, file tree, API operation list, protocol spec, or comparison table that does NOT appear in the section → flag as HIGH severity**
- **If a DEEP topic’s section uses <50% of unique technical material from its extracts → HIGH severity**
- A section that turns 4500 words of detailed technical extracts into 900 words of summary is NOT acceptable

### Structure
- Does the document flow logically from section to section?
- Are subsections within each section coherent?
- Is the Executive Summary accurate and concise?

### Style compliance
- Does the tone match params.md audience?
- Is the language correct (Russian/English as specified)?
- Is the formulas policy followed?

### Word count
- Check each section against its page budget × 300
- Flag sections that are >20% over or under
- Note the overall document word count vs. target

## Example Review

```markdown
## Verdict: REVISE

## Sections to revise
- section: 03_architecture.md | severity: HIGH | issue: Section mentions "distributed sandbox model" but never explains how it works. Need: architecture description, component interaction, security boundaries.
- section: 05_benchmarks.md | severity: MEDIUM | issue: Benchmarks table lacks context — include methodology, test conditions, and analysis of results, not just raw numbers.

## Sections OK: 01, 02, 04, 06, 07

## Overall notes
Strong introduction and comparison sections. The security analysis (04) is particularly well-done with clear examples. Conclusion effectively synthesizes findings. Minor: some Russian grammatical errors in section 06 that could be polished.
```
