---
description: "Section writing protocol for the Writer agent — content depth, word budget, illustration placeholders, revision handling, chunked writing."
---

# Section Writing

## Writing Protocol

### Step 1: Read inputs

1. Read `research/_plan/toc.md` — find your section by `## NN.` heading
2. Read `research/_plan/params.md` — audience, tone, formulas policy, language
3. Read each extract file listed in your section's `Sources:` field
4. If revision: also read `draft/_review.md`

### Step 2: Plan your section

Before writing:
- Identify the key points from the source extracts
- Plan the subsection structure (H3 headings within your H2 section)
- Estimate which points need illustration placeholders
- Calculate target word count from page budget

### Step 3: Write

Write deeply analytical content, not surface-level summaries:

| Aspect | Requirement |
|---|---|
| **Depth** | Explain mechanisms and internals, not just mention them. "X works by storing JSON messages at path Y with schema Z" not "X uses a messaging system" |
| **Technical details** | If extracts contain JSON structures, file paths, CLI commands, config formats, protocol specs — INCLUDE them in your section. These are the most valuable content. |
| **EXTRACT COVERAGE** | You MUST use ALL unique technical material from your source extracts. If an extract contains a JSON schema, a file tree, an API operation list, a comparison table, or a protocol spec — it MUST appear in your section. Summarizing 4500 words of technical extracts into 900 words of prose is UNACCEPTABLE. Include the details. |
| **Budget vs depth** | If your extracts contain more technical material than fits in the page budget, **EXCEED the budget**. It is better to write 1500 words for a 900-word budget than to drop JSON schemas, file structures, or API lists. The Critic will never flag a section for being too detailed. |
| **Examples** | Include concrete examples, code snippets, or case studies from the source material |
| **No filler** | Every sentence must add information. Ban: "powerful", "innovative", "revolutionary", "comprehensive", "cutting-edge", "seamless", "robust", "game-changing". Use: specific facts, numbers, structures. |
| **No marketing copy** | If your paragraph could appear on a product landing page — rewrite it. Replace "X provides a seamless experience" with "X achieves this via Y mechanism with Z trade-offs" |
| **Comparisons** | When comparing alternatives, use structured comparison (tables, pros/cons) |
| **Formulas** | Follow params.md policy — typically minimal, always with intuitive explanation |
| **References** | Integrate source material naturally, don't just list facts |
| **Language** | Write in the language specified in params.md |
| **Tone** | Match the audience from params.md |

### Step 4: Insert illustration placeholders

**MANDATORY for sections with 2+ page budget.** The Illustrator agent depends on your placeholders to know WHAT to generate and WHERE to insert images in the final document. Without placeholders, illustrations won't be embedded.

Insert at points where visual aids would help understanding:

```html
<!-- ILLUSTRATION: type=architecture, section=03, description="Detailed description of what to visualize. Must be 200+ characters. Include: all components to show, relationships/connections between them, suggested visual layout (horizontal flow, vertical hierarchy, etc.), color coding if relevant. The Illustrator needs enough information to create a useful diagram without reading the surrounding text." -->
```

**Type options:** `architecture`, `comparison`, `pipeline`, `flowchart`, `conceptual`, `infographic`, `timeline`

**RULES:**
- Sections with **2-3 page budget**: at least 1 illustration placeholder
- Sections with **4+ page budget**: at least 2 illustration placeholders
- Introduction and Conclusion sections: 0-1 (optional)
- Description: 200+ characters, detailed enough for the Illustrator to work independently
- Place the placeholder BETWEEN paragraphs at the point where the visual best supports the text

### Step 5: Verify content coverage

After writing, check that you used ALL technical artifacts from your source extracts:
- [ ] Every JSON schema/structure from extracts → included in section
- [ ] Every file tree / directory layout → included
- [ ] Every API/tool operation list → included
- [ ] Every comparison table → included or merged with your own
- [ ] Every code example → included
- [ ] Every protocol spec / message format → included

If an extract describes 13 API operations and your section mentions 3 of them — your section is INCOMPLETE. Go back and add the missing ones.

**Coverage target: ≥80% of unique technical details from extracts must appear in the section.** Missing a JSON schema that was in the extract = coverage failure.

## Chunked Writing

Sections over ~3000 words will hit the output token limit. Use this strategy:

1. Write the first ~3000 words of your section
2. End with the marker: `<!-- SECTION_CONTINUES -->`
3. Use `replace_string_in_file` to replace the marker with the next ~2000 words
4. Add another `<!-- SECTION_CONTINUES -->` if more content remains
5. Repeat until the section is complete

## Revision Handling

When the Orchestrator sends you with `revision: true`:

1. Read `draft/_review.md`
2. Find issues mentioning your section filename (e.g., `section: 03_comparison.md`)
3. For each issue:
   - **HIGH severity:** Significant rewrite of the affected subsection
   - **MEDIUM severity:** Expand, improve, or restructure the affected part
4. Rewrite to the SAME file path (overwrite the original)
5. Don't rewrite parts that weren't flagged — focus on the specific issues

## Output Format

Write to `{BASE_FOLDER}/draft/_sections/NN_title.md`:

```markdown
## {Section Title}

{Introduction paragraph setting context}

### {Subsection 1}

{Deep content with examples}

<!-- ILLUSTRATION: type=..., section=NN, description="..." -->

### {Subsection 2}

{More content}

| Comparison | Option A | Option B |
|---|---|---|
| Feature 1 | Detail | Detail |
```

Note: Use H2 (`##`) for the section title, H3 (`###`) for subsections. The Editor will adjust heading levels during merge if needed.

## Special Sections

### Executive Summary (01)

- 200-400 words, no need for source extracts
- Summarize key findings from the full document
- The Writer for this section receives the full ToC as context (no extract files)
- No illustration placeholders needed

### Conclusion (last section)

- 200-400 words, no need for source extracts  
- Synthesize findings and provide actionable recommendations
- The Writer for this section receives the full ToC as context
- No illustration placeholders needed
