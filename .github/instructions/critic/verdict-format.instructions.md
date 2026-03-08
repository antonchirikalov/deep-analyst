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
| **APPROVED** | All sections meet quality bar. Only LOW severity issues remain. | Proceed to Phase 8 (Illustrator) |
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
- **Missing technical details:** extracts contain JSON structures, file paths, protocol specs, but the section just summarizes them in 2 sentences
- Factual gaps: key aspects of the topic are missing
- **Filler content:** sentences like "X использует мощный подход к Y" without explaining what the approach IS
- Style mismatch: wrong tone for the audience, or wrong language
- Word count: a section is >20% over or under budget
- **Total document is <80% of target word count** (e.g., 5500 words for a 25-page target = REVISE)
- **Same content appears in multiple sections** (duplication instead of depth)
- Poor structure within a section (jumping between unrelated ideas)

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
- `<!-- ILLUSTRATION: ... -->` placeholder comments — these are for the Illustrator (Phase 8)
- `![Рис. N]` image references that don't resolve yet — images are generated in Phase 8
- Minor formatting that the Editor handles (heading levels, spacing)

## Evaluation Criteria

### Content quality (most important)
- Are mechanisms explained with HOW-level depth? (not just "uses a mailbox" but "messages stored as JSON at ~/.claude/mailbox/{id}/inbox/, containing fields: sender, recipient, content, timestamp")
- Are there concrete examples, data points, or code snippets FROM THE SOURCE MATERIAL?
- Is the content accurate based on the source material?
- Does each section add **unique** value? (Same content in sections 3 and 8 = duplication)
- Is there filler/marketing language? ("мощный", "инновационный", "comprehensive", "революционный" without substance)

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
