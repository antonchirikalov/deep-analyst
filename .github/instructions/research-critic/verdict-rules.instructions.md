---
description: Verdict definitions, severity levels, and structured output format for Research Critic reviews.
---

# Verdict Rules

## Verdicts

| Verdict | Meaning | Outcome |
|---------|---------|---------|
| **APPROVED** | Document is ready for user delivery | Orchestrator copies to FINAL_REPORT.md |
| **REVISE** | Issues found, fixable from existing research | Analyst revises draft, optionally Illustrator regenerates |
| **REJECTED** | Significant gaps requiring additional research | Scout relaunches, then full cycle repeats |

### When to APPROVE
- No CRITICAL issues
- No MAJOR issues (or all previous MAJOR issues resolved)
- Only MINOR polish issues remain (acceptable to deliver)

### When to REVISE
- Issues are fixable by Analyst without new research: restructuring, rewording, adding missing analysis from existing data
- Source quality issues that can be addressed by better citation
- Missing diagram types or sections that can be filled from existing research

### When to REJECT
- Significant topic gaps that require additional Scout research
- Multiple unreliable sources that need replacement with authoritative ones
- Fundamental misunderstanding of the topic requiring fresh research

## Severity Levels

| Severity | Definition | Examples |
|----------|-----------|---------|
| **CRITICAL** | Structural or factual failure that makes the document unusable | Missing required sections, factual errors, fundamentally broken logic |
| **MAJOR** | Significant quality gap that materially affects document value | Missing citations for key claims, unbalanced coverage, vague generic conclusions |
| **MINOR** | Polish issue that doesn't affect the core value | Grammar improvements, minor formatting, wording suggestions |

## Output Format

Return review in response text (NOT as a separate file):

```
=== RESEARCH REVIEW — Iteration N/3 ===
VERDICT: [APPROVED / REVISE / REJECTED]
ILLUSTRATION_ISSUES: [YES / NO]

ISSUES TABLE:
| # | Severity | Section | Tag | Issue | Required Action |
|---|----------|---------|-----|-------|-----------------|
| 1 | MAJOR | §5 | [SOURCE] | Missing citation for 40% efficiency claim | Add source URL from research files |
| 2 | MINOR | §3 | [TEXT] | Paragraph too long (8 sentences) | Split into two paragraphs |

Tags: [TEXT], [SOURCE], [LOGIC], [ILLUSTRATION]

STRENGTHS:
- Excellent comparison table with clear criteria
- Strong Executive Summary

Total: 0 CRITICAL, 1 MAJOR, 1 MINOR
=== END RESEARCH REVIEW ===
```

## Issue Tags

| Tag | When to Use |
|-----|------------|
| `[TEXT]` | Structure, formatting, language, readability issues |
| `[SOURCE]` | Missing citations, unreliable sources, outdated references |
| `[LOGIC]` | Contradictions, unsupported claims, logical gaps |
| `[ILLUSTRATION]` | Missing, misaligned, or inadequate illustrations |

## ILLUSTRATION_ISSUES Field

- `ILLUSTRATION_ISSUES: NO` — illustrations are adequate, no Illustrator re-run needed
- `ILLUSTRATION_ISSUES: YES` — signal for Orchestrator to relaunch Illustrator

Set to YES when:
- Required diagram types are missing for the document type
- Illustrations don't match their section content
- Manifest descriptions indicate poor prompt-to-content alignment

## Iteration Behavior

- **Iteration 1:** Comprehensive initial review — check everything
- **Iterations 2–3:** Focus on resolving previous issues
  - Mark each previous issue as RESOLVED or PERSISTENT
  - Acknowledge improvements explicitly
  - Check for new regressions introduced by fixes
  - Escalate if same issues persist across 2+ iterations
