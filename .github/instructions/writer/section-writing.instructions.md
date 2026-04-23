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

### Step 2b: Gap-filling search (optional)

If the source extracts are **insufficient** for the depth expected by the page budget, you may search for additional information:

| Tool | When to use | Budget |
|---|---|---|
| `tavily_search` | Missing context, need overview or docs | Max 3 queries per section |
| `fetch_webpage` | Need full text from a specific URL found in extracts | Max 3 fetches per section |
| `mcp_github_search_code` | Need real code examples, configs, implementations | Max 2 queries per section |
| `mcp_github_get_file_contents` | Need a specific file from a known repo | Max 3 reads per section |
| `mcp_huggingface_hub_repo_search` | Need model cards, dataset info | Max 2 queries per section |
| `mcp_huggingface_paper_search` | Need recent research or benchmarks | Max 2 queries per section |

**Rules:**
- Only search if extracts give you <60% of what you need for target word count
- Total search calls per section: **max 8** (across all tools)
- Log every search in debug trace with what you were looking for and what you found
- Prefer GitHub for code/config examples, HuggingFace for ML specifics, tavily for general context

### Step 3: Write

> **CRITICAL RULE — SUBSECTION STRUCTURE**
>
> Every H3 subsection (### heading) MUST follow this template:
>
> 1. **Conceptual introduction** (2-3 paragraphs) — Write as if explaining to a brilliant colleague from an adjacent field. Start with the PROBLEM this concept solves, then explain the IDEA behind the solution. Use vivid analogies that make the reader say "aha, now I get it". Aim for the quality of the best technical writing — Feynman lectures, Karpathy blog posts, 3Blue1Brown narratives. The reader who has never encountered this term should finish these paragraphs thinking "this is elegant, I see why this exists."
> 2. **How it works** (2-4 paragraphs) — Walk through the mechanism as a story with a concrete example. "Imagine a model processing the sentence 'The cat sat on the...'. At position 6, the model needs to attend to all 5 previous tokens. Without caching, it would recompute Key and Value projections for all of them — wasteful, like re-reading an entire book every time you turn a page..." Make it visual, sequential, tangible.
> 3. **Technical details** (1+ paragraphs) — Now that the reader understands the concept, go deep: numbers, configurations, code snippets, comparison tables, architecture specifics.
> 4. **Formula** (OPTIONAL, max 1 per subsection) — Only after the reader fully understands the concept. A formula should feel like a concise summary of what they already know, not new information. Introduce it: "We can express this more precisely: ..." — never drop a formula without a bridge sentence.
>
> **The gold standard:** After reading steps 1-2, the reader should be able to explain the concept to someone else in their own words — even without the formula. The formula is a bonus for precision, not the explanation itself.
>
> **VIOLATION (HIGH severity at review):** Starting a subsection with a formula, math notation, or a sentence like "For each position $i$..." / "Formally, we define..." without prior plain-language explanation. This is the #1 quality issue.

Write deeply analytical content, not surface-level summaries:

| Aspect | Requirement |
|---|---|
| **Depth** | Explain mechanisms and internals, not just mention them. Start every concept with INTUITIVE UNDERSTANDING: what it is, why it exists, what problem it solves. Then go deeper into how it works. "X works by storing JSON messages at path Y with schema Z" not "X uses a messaging system". The reader must understand the WHY before seeing the HOW. |
| **Technical details** | If extracts contain JSON structures, file paths, CLI commands, config formats, protocol specs — INCLUDE them in your section. These are the most valuable content. |
| **Examples** | Include concrete examples, code snippets, or case studies from the source material |
| **No filler** | Every sentence must add information. Ban: "powerful", "innovative", "revolutionary", "comprehensive". Use: specific facts, numbers, structures. |
| **No timelines** | Do NOT include implementation timelines, effort estimates, sprint plans, or project schedules unless the user's prompt or params.md explicitly requests them. |
| **Comparisons** | When comparing alternatives, use structured comparison (tables, pros/cons) |
| **Formulas** | **CONCEPT FIRST, FORMULA LAST.** Never open a subsection with a formula or equation. Every formula MUST be preceded by at least 2 paragraphs of plain-language explanation: what the concept means intuitively, why it matters, and a real-world analogy. Max 2-3 formulas per section. Source extracts often contain dense math — your job is to EXPLAIN, not transcribe. Convert formulas into intuitive understanding. Example: instead of immediately showing `mem = 2 × n_layers × d_model × seq_len × sizeof(dtype)`, first explain: "KV-кеш — это таблица ключей и значений, которую модель запоминает, чтобы не пересчитывать attention для уже обработанных токенов. На каждом слое для каждого токена хранятся два вектора (Key и Value)..." and only then, optionally, show the formula. If params.md says "minimal" or "avoid" — prefer prose analogies and only include formulas that a reader truly cannot understand without. |
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

### Step 5: Add transition ending

End your section with a 1-2 sentence transition to the next topic. This is essential because
sections are merged mechanically (concatenation), not by an Editor agent. The transition should
briefly hint at what follows without repeating content.

Example: "Having examined the internal architecture, we now turn to how these components interact in production environments."

### Step 6: Verify word count

After writing, estimate your word count:
- Target: `pages × 300` (from ToC)
- Tolerance: ±15%
- If >15% over: trim less critical content
- If >15% under: expand explanations, add examples

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

*Рис. N. Short caption describing the illustration*

### {Subsection 2}

{More content}

| Comparison | Option A | Option B |
|---|---|---|
| Feature 1 | Detail | Detail |
```

**Caption rule:** Every `<!-- ILLUSTRATION: ... -->` placeholder MUST be followed by a visible italic caption line `*Рис. N. Caption*` (or `*Fig. N. Caption*` for English documents). The Illustrator will replace the HTML comment with the image link but keep the caption line. Number illustrations sequentially within the full document (across all sections).

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
