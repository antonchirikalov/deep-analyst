---
description: Full validation checklist for Research Critic — structure validation, content review, illustration assessment.
---

# Review Checklist

## Step 1: Structure Validation (MANDATORY FIRST)

Check document matches expected template. If ANY structural issue → CRITICAL.

### All Document Types
- [ ] Executive Summary present (5–7 sentences)
- [ ] Heading hierarchy correct (H1→H2→H3)
- [ ] All required sections from template present
- [ ] Sources section at end with URLs and descriptions
- [ ] No orphaned sections (heading without content)

### Comparative Analysis
- [ ] Comparison Methodology section present
- [ ] Participant Overview with subsection per technology
- [ ] Comparison Table present
- [ ] Detailed Comparison by Criteria with subsections
- [ ] Use Cases section
- [ ] Conclusions and Recommendations

### Technology Overview
- [ ] Historical Background section
- [ ] Architecture / How It Works section
- [ ] Advantages and Limitations section
- [ ] Development Prospects section

### State of the Art
- [ ] Evolution of Approaches section
- [ ] Current Leading Methods with subsections
- [ ] Benchmarks and Metrics section
- [ ] Open Problems section
- [ ] Promising Directions section

### Research Report
- [ ] Abstract section
- [ ] Problem Statement section
- [ ] Literature Review section
- [ ] Results and Data section
- [ ] Discussion section
- [ ] Research Limitations section

## Step 2: Content Review

Only proceed here if Step 1 passes.

### Logical Coherence
- [ ] Arguments flow logically from section to section
- [ ] No internal contradictions
- [ ] Claims supported by evidence from within the document
- [ ] Conclusions follow from the analysis presented

### Source Quality
- [ ] Majority of sources are authoritative (official docs, papers, vendor sites)
- [ ] Source URLs are present and look valid
- [ ] No unsourced factual claims
- [ ] Sources are recent (within last 2–3 years for tech topics)
- [ ] Multiple perspectives represented (not just one vendor/author)

### Topic Coverage
- [ ] All subtopics from Scout research reflected in document
- [ ] No major aspect of the topic is missing
- [ ] Depth appropriate for the document type

### Opinion Balance
- [ ] Pros AND cons presented for each approach
- [ ] No single technology/approach unfairly favored
- [ ] Trade-offs explicitly discussed
- [ ] Recommendations are justified, not just asserted

### Conclusion Clarity
- [ ] Conclusions are specific, not generic
- [ ] Backed by evidence from the document body
- [ ] Actionable recommendations with clear use cases
- [ ] Limitations acknowledged

### Illustration Placeholders
- [ ] 3–5 `<!-- ILLUSTRATION: ... -->` placeholders present
- [ ] Each placeholder has `type`, `section`, and `description` (200+ chars)
- [ ] Placeholder descriptions are specific (elements, connections, layout, colors)
- [ ] Required illustration types present for document type
- [ ] Caption line `*[Рис. N. ...]*` present below each placeholder

## Step 3: Illustration Review

- [ ] `illustrations/_manifest.md` exists
- [ ] Required illustration types present for document type
- [ ] Illustrations align with section content (per manifest descriptions)
- [ ] No duplicate or redundant illustrations
- [ ] If illustrations are inadequate → tag issues with `[ILLUSTRATION]`
