---
description: "Per-topic structure analysis protocol for the Analyst agent — depth assessment, section proposals, source mapping, cross-references."
---

# Structure Analysis

## Analysis Protocol

### Step 1: Read all extracts

Read every `extract_*.md` file in your subtopic folder. Note:
- Total word count across all extracts
- Number of distinct sources
- Key topics covered

### Step 2: Assess depth

Rate the available material:

| Level | Criteria | What to report |
|---|---|---|
| **DEEP** | 3+ quality extracts, comprehensive coverage of the topic | Full details: can support 3-5 document pages |
| **MEDIUM** | 2+ extracts, decent coverage but notable gaps | Partial: can support 1-3 pages, note gaps |
| **SHALLOW** | 1 extract or thin material across multiple | Limited: merge with neighbor, note what's missing |
| **INSUFFICIENT** | No usable content or all extracts are off-topic | Skip: Planner should merge or drop this subtopic |

### Step 3: Propose sections

For each potential document section this material can support:

1. **Title** — clear, descriptive section name
2. **Description** — one line explaining what this section covers
3. **Source mapping** — which extract file(s) provide the material, and what specific content from each:
   ```
   Sources: extract_1.md (key: architecture diagram, component list),
            extract_3.md (key: performance benchmarks, latency data)
   ```
4. **Estimated size** — rough page count this section could fill

### Step 4: Identify cross-references

Look for overlaps with other subtopics:
- Content that clearly relates to another search subtopic
- Shared concepts that the Planner should merge
- Potential conflicts or contradictions between sources

### Step 5: Key findings

Bullet points summarizing the most important discoveries:
- Surprising findings
- Key numbers/benchmarks
- Gaps in the available literature
- Recommended focus areas for the document

## Output Format

```markdown
# Structure: {subtopic_name}

## Depth: {DEEP | MEDIUM | SHALLOW | INSUFFICIENT}

## Proposed sections
1. {Section title} — {description}
   Sources: extract_1.md (key: {specific content}), extract_3.md (key: {specific content})
2. {Section title} — {description}
   Sources: extract_2.md (key: {specific content})

## Cross-references
- Overlaps with subtopic: {name} on topic: {shared topic}
- {Another cross-reference}

## Key findings
- {finding 1}
- {finding 2}
- {finding 3}
```

## Context Overflow Protection

If total extract content exceeds 20K words:
1. Prioritize extracts marked with higher word counts (deeper content)
2. For lower-priority extracts, skim headings and key sections only
3. Note in your output which extracts were fully vs. partially analyzed
