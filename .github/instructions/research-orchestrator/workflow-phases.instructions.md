---
description: "Full 10-phase workflow execution protocol for the Research Orchestrator — phase ordering, sub-agent prompting, inter-phase validation, and revision loop."
---

# Workflow Phases

## CRITICAL: ALL PHASES ARE MANDATORY

Every document — brief (5 pages), standard (20 pages), or detailed (30 pages) — runs ALL 10 phases. "Brief" means fewer pages in the output, NOT fewer phases in the pipeline. The Orchestrator MUST NEVER consolidate, skip, or substitute for any phase.

## Phase Execution Protocol

Execute phases sequentially. Validate outputs between phases. Log every transition.

### Phase 0: Decomposition (Orchestrator)

1. Generate timestamp: `YYYYMMDD_HHMMSS`
2. Create BASE_FOLDER: `generated_docs_{timestamp}/`
3. Initialize workflow log:
   ```bash
   python3 .github/skills/workflow-logger/scripts/workflow-logger.py init \
     --folder $BASE_FOLDER --project "$TITLE"
   ```
4. Parse user request into parameters:
   - `max_pages` — see size tier table in agent file
   - `audience`, `tone`, `formulas`, `language`
5. Write `research/_plan/params.md`:
   ```markdown
   # Research Parameters
   
   - **Topic:** {main topic}
   - **Max pages:** {N}
   - **Audience:** {target audience}
   - **Tone:** {academic | business | conversational}
   - **Formulas:** {minimal with explanations | none | as needed}
   - **Language:** {Russian | English | ...}
   
   ## Subtopics
   1. {subtopic_1}
   2. {subtopic_2}
   ...
   ```
6. Log via agent-trace: `--action write --target "research/_plan/params.md"`

### Phase 1: Retrieval (Retriever × N, parallel)

Launch one Retriever per subtopic, all in parallel.

**Prompt template:**
```
BASE_FOLDER: {absolute_path}
Search for URLs about: "{subtopic_name}"
Write results to: research/{subtopic_slug}/_links.md
```

**Validation after Phase 1:**
```bash
python3 .github/skills/workflow-logger/scripts/agent-trace.py check \
  --folder $BASE_FOLDER --file "research/{subtopic}/_links.md"
```
- Present and non-empty → proceed
- Missing or empty → skip this subtopic in Phases 2-3, log warning

### Phase 2: Extraction (Extractor × N, parallel)

Launch one Extractor per subtopic (only for subtopics with valid `_links.md`).

**Prompt template:**
```
BASE_FOLDER: {absolute_path}
Subtopic: {subtopic_name}
Read URLs from: research/{subtopic_slug}/_links.md

OUTPUT RULES (MANDATORY — violation = pipeline failure):
1. Write ONE SEPARATE FILE PER URL: extract_1.md for the 1st URL, extract_2.md for the 2nd URL, etc.
   NEVER combine multiple URLs into one file. If _links.md has 8 URLs → produce 8 files.
2. Each extract file: 2000-4000 words. COPY content verbatim from the source.
   Do NOT summarize. If tavily_extract returns 3000 words, your file must contain ~3000 words.
3. Include ALL code blocks, JSON structures, file paths, CLI commands, config examples verbatim.
4. If a URL fails (403/404/timeout), skip it and log — but continue to the NEXT URL.
```

**Validation after Phase 2 (ENFORCE):**
- Count URLs in each `_links.md` (grep for `https://` | wc -l)
- Count `extract_*.md` files in each subtopic folder
- **If extract_count < url_count × 0.5 AND extract_count < 3:** re-run Extractor for that subtopic with explicit reminder: "You wrote {N} extracts but there are {M} URLs. Write one file per URL."
- Check word counts: `wc -w research/{subtopic}/extract_*.md`. If average < 500 words, log warning "Extractor is summarizing instead of extracting."
- Skip subtopics with no extracts in Phase 3
- **Even if no extracts exist: still proceed to Phase 3 (Analyst marks INSUFFICIENT), then Phase 4, etc. NEVER skip phases.**

### Phase 3: Analysis (Analyst × N, parallel)

Launch one Analyst per subtopic (only for subtopics with extracts).

**Prompt template:**
```
BASE_FOLDER: {absolute_path}
Analyze all extracts in: research/{subtopic_slug}/
Write structure analysis to: research/{subtopic_slug}/_structure.md
Overall research topic: "{main_topic}"
```

**Validation after Phase 3:**
- Check each `_structure.md` exists
- Log warning for missing ones; Planner works with what exists

### Phase 4: Planning (Planner × 1)

**Prompt template:**
```
BASE_FOLDER: {absolute_path}
Read all research/*/_structure.md files and research/_plan/params.md.
Build unified Table of Contents.
Write to: research/_plan/toc.md
```

**Validation after Phase 4:**
- `toc.md` exists and contains `## 01.` heading
- Total pages in ToC matches params.md max_pages (±1)

### Phase 5: Writing (Writer × M, parallel)

Parse `toc.md` to find all `## NN.` sections. Launch one Writer per section, all in parallel.

**Prompt template (initial):**
```
BASE_FOLDER: {absolute_path}
Write section: {NN}. {Section Title}
Page budget: {N} pages ({N×300} words) — this is the MINIMUM word count for your section.
Source files: {comma-separated paths from Sources field}
Read params from: research/_plan/params.md
Write to: draft/_sections/{NN}_{slug}.md

MANDATORY RULES:
1. WORD COUNT: Your section MUST be at least {N×300} words. A 3-page budget = 900+ words. Check with wc -w before finishing.
2. TECHNICAL DEPTH: Include ALL technical details from extracts — code blocks, JSON structures, file paths, CLI commands, config examples. Copy them verbatim, do not paraphrase into vague summaries.
3. ILLUSTRATION PLACEHOLDERS: Include at least 1 placeholder per 2+ page section:
   <!-- ILLUSTRATION: type="architecture|comparison|pipeline|flowchart", section="{NN}. {Title}", description="Detailed description of what to visualize, 200+ chars" -->
   Place them where a diagram would help explain architecture or flow.
4. NO FILLER: Every sentence must add information. No "мощный", "инновационный", "comprehensive".
```

**Prompt template (revision):**
```
BASE_FOLDER: {absolute_path}
Write section: {NN}. {Section Title} — REVISION
This is a revision. Read draft/_review.md for Critic's feedback on your section.
Page budget: {N} pages ({N×300} words) — this is the MINIMUM word count.
Source files: {paths}
Read params from: research/_plan/params.md
Write to: draft/_sections/{NN}_{slug}.md
revision: true

MANDATORY: Address ALL Critic feedback points. Ensure section has {N×300}+ words.
Include <!-- ILLUSTRATION: ... --> placeholders if missing.
Include ALL technical details from extracts — code, JSON, paths, commands.
```

**Validation after Phase 5 (ENFORCE):**
- All expected `_sections/NN_*.md` files exist
- If a file is missing: retry that Writer ONCE. If still missing → skip + log error.
- **Word count check for each section:** run `wc -w draft/_sections/*.md`. If any section is <60% of its page budget × 300 words, log warning with section name and actual vs expected count.
- **ILLUSTRATION placeholder check:** run `grep -c 'ILLUSTRATION' draft/_sections/*.md`. If ZERO placeholders across ALL sections:
  1. Log error: "Writers produced 0 illustration placeholders — Illustrator will use fallback mode"
  2. Do NOT re-run Writers for this — the Illustrator has fallback logic to identify sections needing diagrams independently.

### Phase 6: Editing (Editor × 1)

**Prompt template:**
```
BASE_FOLDER: {absolute_path}
Merge all draft/_sections/*.md files in ToC order.
Read ToC from: research/_plan/toc.md
Read params from: research/_plan/params.md
Write merged document to: draft/v1.md
```

**Validation after Phase 6:**
- `draft/v1.md` exists and word count is reasonable (>50% of target)
- **Word count check:** target = `max_pages × 300`. If v1.md is <60% of target → log warning. For "подробный" (25-30 pages), expect ≥7000 words. For "стандартный" (15-20 pages), expect ≥4000 words.
- If word count is severely under target, the Critic will catch it in Phase 7 and request revisions.

### Phase 7: Review (Critic × 1)

**Prompt template:**
```
BASE_FOLDER: {absolute_path}
Review: draft/v1.md
Parameters: research/_plan/params.md
ToC with budgets: research/_plan/toc.md
Write review to: draft/_review.md
```

**After Critic finishes:**
1. Read `draft/_review.md`
2. Find `## Verdict:` line
3. Parse verdict: APPROVED / REVISE / REJECTED

**If APPROVED:** Proceed to Phase 8.

**If REVISE or REJECTED:**
- Log revision via `workflow-logger.py verdict`
- Parse `## Sections to revise` for section filenames and issues
- Re-run ONLY the listed Writers (with revision flag) → Phase 5 (partial)
- Re-run Editor → Phase 6
- Re-run Critic → Phase 7
- **Max 2 revision loops.** After 2 loops → accept as-is, log warning:
  ```bash
  python3 .github/skills/workflow-logger/scripts/agent-trace.py log \
    --folder $BASE_FOLDER --agent Orchestrator --phase 7 \
    --action skip --status warn --detail "Max revisions reached, accepting draft as-is"
  ```

### Phase 8: Illustration (Illustrator × 1)

**MANDATORY** — skip only if OPENAI_API_KEY is missing (check via env var).

**Prompt template:**
```
BASE_FOLDER: {absolute_path}
Generate illustrations for the final draft: draft/v1.md

STEPS (ALL MANDATORY):
1. Read draft/v1.md, find <!-- ILLUSTRATION: ... --> placeholders.
2. If NO placeholders found: independently identify 3-5 sections that need architecture/comparison/pipeline diagrams.
3. For each illustration: run paperbanana_generate.py with --direct mode and a SHORT 2-4 sentence prompt.
4. If paperbanana fails: FALLBACK to Mermaid diagrams — generate mermaid code blocks and embed them DIRECTLY in draft/v1.md.
5. EMBED every illustration in draft/v1.md using replace_string_in_file:
   - PNGs: replace placeholder or insert ![Рис. N](../illustrations/NN_name.png) near the relevant H2
   - Mermaid fallback: insert ```mermaid code blocks directly into the document
6. Write manifest to: illustrations/_manifest.md
7. VERIFY: read draft/v1.md and confirm it contains either PNG references or mermaid blocks. If ZERO visual content → YOUR RUN FAILED. Go back and embed.
```

**Validation after Phase 8 (ENFORCE):**
- Check `draft/v1.md` for visual content: `grep -c 'png\|mermaid' draft/v1.md`
- **If zero matches:** The Illustrator failed to embed. Log error.
- If PNG files exist in `illustrations/` but v1.md has no references: the Orchestrator MUST manually insert image references using `replace_string_in_file`.

### Phase 9: Delivery (Orchestrator)

1. Log pipeline completion:
   ```bash
   python3 .github/skills/workflow-logger/scripts/workflow-logger.py event \
     --folder $BASE_FOLDER --message "Pipeline complete. Final document: draft/v1.md"
   ```
2. Report to user:
   - Final document path
   - Page count and word count
   - Number of illustrations generated
   - Any warnings or skipped subtopics
   - Mention PDF export availability via `@PDF Exporter`

## Error Recovery

| Scenario | Action |
|---|---|
| Sub-agent crashes mid-execution | Check what files were written; retry agent once |
| Validation fails (missing output) | Skip subtopic/section, log error, continue pipeline |
| Max revision loops exceeded | Accept draft as-is, log warning |
| OPENAI_API_KEY missing (Phase 8) | Skip illustrations, log error, deliver text-only document |
