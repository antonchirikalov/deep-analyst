---
description: "Document merge rules for the Editor agent — assembly order, deduplication, transitions, executive summary generation, illustration placeholder preservation."
---

# Merge Rules

## Assembly Protocol

### Step 1: Read inputs

1. Read `research/_plan/toc.md` — defines section order
2. Read `research/_plan/params.md` — max_pages, document title, language
3. List all files in `draft/_sections/` via `list_dir`
4. Read each section file in ToC order

### Step 2: Plan the merge

Before writing:
- Note any overlapping content between sections
- Identify where transitions are needed
- Check total word count vs. target (max_pages × 300)
- Verify all expected section files are present

### Step 3: Assemble

Write `draft/v1.md` with this structure:

```markdown
# {Document Title}

## Executive Summary

{200-400 word summary — synthesize from all sections}

{Section 02 content}

{Transition sentence}

{Section 03 content}

...

{Final section / Conclusion content}
```

### Step 4: Deduplication

Different Writers may have covered overlapping material:
- **Identical content:** Remove the duplicate entirely from the later section
- **Similar but complementary:** Keep both but rephrase to avoid repetition
- **Contradictory:** Keep the version with better sourcing, add a brief note about alternative perspectives

### Step 5: Transitions

Add 1-2 sentence transitions between major sections. Examples:
- "Building on the architecture described above, we now examine..."
- "Having established the theoretical foundation, let's turn to practical benchmarks..."
- Keep transitions brief — they should guide the reader, not add filler

### Step 6: Word count compliance

| Situation | Action |
|---|---|
| Total >10% over target | Trim: shorten verbose explanations, remove redundant examples |
| Total >15% under target | Flag in agent-trace log — content may be too thin |
| Individual section wildly over/under | Note but don't force-trim — the Critic will catch this |

## Illustration Placeholder Preservation

**CRITICAL:** Preserve ALL `<!-- ILLUSTRATION: ... -->` comments exactly as written by Writers:

- Do NOT remove them
- Do NOT modify the attributes
- Do NOT treat them as content errors or broken HTML
- They will be replaced by the Illustrator in Phase 8

If you see `<!-- ILLUSTRATION: ... -->` followed by a caption line like `*[Рис. N. Caption]*`, preserve both.

## Heading Level Normalization

Writers use H2 (`##`) for section titles, H3 (`###`) for subsections. In the merged document:
- Document title: H1 (`#`)
- Section titles: H2 (`##`)
- Subsections: H3 (`###`)
- Sub-subsections: H4 (`####`)

Adjust heading levels if any Writer used non-standard levels.

## Chunked Writing Strategy

The merged document WILL exceed 3000 words. You MUST use chunked writing:

1. **First chunk (~3000 words):** Title + Executive Summary + first 2-3 sections
   - End with: `<!-- SECTION_CONTINUES -->`
2. **Subsequent chunks (~2000 words each):** Use `replace_string_in_file` to replace the marker
   - Add a new `<!-- SECTION_CONTINUES -->` if more content follows
3. **Final chunk:** Last section(s) + Conclusion — no marker at end

This prevents the output token limit crash (Known Issue #7).

## Re-merge on Revision

When the Critic requests revisions and Writers rewrite their sections:
- Re-read ALL section files (including unchanged ones)
- Re-merge from scratch — don't try to patch the existing v1.md
- Write to the same path: `draft/v1.md` (overwrite)
- Previous content is preserved in `_review.md` as feedback context

## Quality Checklist

Before finishing:
- [ ] All ToC sections present in the document
- [ ] No duplicate content between sections
- [ ] Smooth transitions between major sections
- [ ] Executive Summary present and concise (200-400 words)
- [ ] ALL `<!-- ILLUSTRATION: ... -->` placeholders preserved
- [ ] Heading levels consistent
- [ ] Total word count within 10% of target
- [ ] Written in the correct language (params.md)
