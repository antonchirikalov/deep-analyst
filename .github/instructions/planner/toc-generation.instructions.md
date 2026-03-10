---
description: "Unified Table of Contents generation rules for the Planner agent — document architecture, page budget allocation, source assignment."
---

# ToC Generation

## Design Principles

1. **Document sections ≠ search subtopics.** You are building a document for a READER, not mirroring the search structure. Reorganize for logical flow and narrative coherence.
2. **Reader experience first.** The document should tell a story: introduce → detail → compare → conclude.
3. **Budget discipline.** All page counts must sum to `max_pages` from params.md (±1 page tolerance).

## Standard Document Structure

Most research documents follow this template (adapt as needed):

```
01. Executive Summary (1-2 pages)
02. Introduction / Background (1-2 pages)
03-N. Main content sections (bulk of pages)
N+1. Conclusion / Recommendations (1-2 pages)
```

Executive Summary is ALWAYS section 01. Conclusion is ALWAYS the last section.

## Section Design

### Merging strategies

| Situation | Action |
|---|---|
| Two subtopics overlap significantly | Merge their extracts into one section |
| Subtopic marked SHALLOW | Combine with a related stronger section |
| Subtopic marked INSUFFICIENT | Drop entirely, or add as brief subsection within a related section |
| One subtopic supports 4+ sections | Split into multiple document sections |

### Source assignment

For each section, list ALL extract files it should draw from. Use full relative paths from BASE_FOLDER:

```
Sources: [research/architecture/extract_1.md, research/security/extract_2.md]
```

A Writer reads ONLY these files — if a relevant extract is not listed, the Writer won't see it.

### Page budget allocation

Budget MUST be driven by the **depth assessment** in each `_structure.md`, not uniform distribution.

#### Depth-based minimum pages

| Analyst depth | Min pages | Rationale |
|---|---|---|
| **DEEP** (3+ extracts, 3000+ words of source material) | **4 pages** | Rich material deserves full coverage |
| **MEDIUM** (2+ extracts, decent coverage) | **2-3 pages** | Solid but not exhaustive |
| **SHALLOW** (1 extract or thin material) | **1 page** | Merge with neighbor |
| **INSUFFICIENT** | **0** | Drop or fold into related section |

These are MINIMUMS. If the Analyst proposed 8+ subsections for a DEEP topic, allocate 5-6 pages.

#### Budget priority rule

When `max_pages` is tight, CUT from Introduction, Conclusion, and SHALLOW sections FIRST. NEVER cut a DEEP topic below 4 pages to make room for boilerplate sections.

| Section type | Typical budget |
|---|---|
| Executive Summary | 1 page (never more) |
| Introduction | 1 page (keep minimal) |
| Core technical section (DEEP) | 4-6 pages |
| Core technical section (MEDIUM) | 2-3 pages |
| Comparison/analysis section | 2-4 pages |
| Conclusion | 1 page (keep minimal) |

Formula: `words = pages × 300`

Verify: sum of all section pages = `max_pages` (±2 — prefer over-budget over shallow content).

#### Anti-pattern: uniform distribution

DO NOT split pages equally across sections. A document with 8 sections and 25 pages should NOT have each section get ~3 pages. DEEP topics with 11 proposed subsections and 4500 words of source material MUST get more than a SHALLOW topic with 1 extract.

## Output Format

```markdown
# Table of Contents
Total pages: {N}
Words per page: 300

## 01. Executive Summary
Pages: 1 (300 words)
Sources: []
Description: High-level summary of key findings. Writer generates from full ToC + params.

## 02. {Section Title}
Pages: {N} ({N×300} words)
Sources: [research/{subtopic}/extract_1.md, research/{subtopic}/extract_3.md]
Description: {What this section covers and why}

## 03. {Section Title}
Pages: {N} ({N×300} words)
Sources: [research/{subtopic}/extract_2.md, research/{other}/extract_1.md]
Description: {What this section covers}

...

## {NN}. Conclusion
Pages: 1 (300 words)
Sources: []
Description: Summary of findings and recommendations. Writer synthesizes from previous sections.
```

### Field requirements

- **Pages:** integer, with word count in parentheses
- **Sources:** array of relative paths from BASE_FOLDER. Empty `[]` for Executive Summary and Conclusion (Writers synthesize these from other context)
- **Description:** 1-2 sentences explaining scope and focus

## Quality Checks Before Writing

1. All extract files referenced in Sources actually exist (you read the _structure.md files which list them)
2. No extract file is orphaned (every relevant extract appears in at least one section's Sources)
3. Total pages sum matches max_pages (±1)
4. Section numbering is sequential with no gaps
5. Executive Summary is 01, Conclusion is last
