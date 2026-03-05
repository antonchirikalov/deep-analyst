---
description: Workflow phase definitions and transition rules for the Research Orchestrator multi-agent pipeline.
---

# Workflow Phases

## Phase Overview

```
Phase 0: Clarify Parameters → Phase 1: Scout (PARALLEL) → Phase 2: Analyst → Phase 3: Illustrator → Phase 4: Critic (iterative) → Phase 5: Delivery
```

## Phase 0: Clarify Parameters

**Trigger:** User provides a research topic.

**Actions:**
1. Parse the user query for explicit document size preference (e.g., "short", "brief", "detailed", "comprehensive", page count)
2. If document size is NOT explicitly specified in the query, ask the user:
   > What document size do you prefer?
   > - **Brief** (~15–20 pages) — key findings and comparisons
   > - **Standard** (~40 pages) — full analysis with illustrations
   > - **Detailed** (~60–100 pages) — deep research with comprehensive coverage
3. Map the user's choice to `max_pages` and `max_words` parameters (1 page ≈ 400 words)
4. Record `max_pages` and `max_words` in workflow_log.md

**Mapping:**
| User Choice | max_pages | max_words | content_depth |
|------------|-----------|----------|---------------|
| Brief / short | 20 | 8000 | conceptual |
| Standard / normal (default) | 40 | 16000 | balanced |
| Detailed / comprehensive | 80 | 32000 | deep |
| Explicit number (e.g., "50 pages") | Use as-is | pages × 400 | balanced (or deep if >60 pages) |

**Transition to Phase 1:** Parameters clarified, `max_pages`, `max_words`, and `content_depth` are set.

## Phase 1: Scout (Parallel Search)

**Trigger:** Orchestrator has decomposed the topic into subtopics with priorities.

**Actions:**
1. Launch one Scout subagent per subtopic IN PARALLEL
2. Each Scout receives: `{ subtopic, priority, output_path }`
3. Wait for ALL Scouts to complete
4. Log results to workflow_log.md

**Transition to Phase 2:** All Scout files written to `research/`

**Failure handling:** If a Scout fails, retry once. If still fails, proceed with available research and note the gap.

## Phase 2: Analyst (Synthesis)

**Trigger:** All research files available in `research/`

**Actions:**
1. Activate Analyst with document type, research folder path, `max_words` constraint, and **`content_depth` parameter**
2. Analyst reads all `research/*.md` files
3. Analyst synthesizes and writes `draft/v1.md` respecting the word limit and content depth tier
4. **Verify:** illustration placeholder count matches the content_depth expectations (conceptual: 5–7, balanced: 4–6, deep: 5–8)
5. Log draft creation to workflow_log.md

**Transition to Phase 3:** Draft file exists at `draft/v1.md`

## Phase 3: Illustrator (Diagram Generation)

**Trigger:** Draft document is ready

**Actions:**
1. Activate Illustrator with draft path
2. Illustrator reads draft, plans diagrams, generates candidates, selects best
3. Illustrator saves PNGs to `illustrations/` and creates `_manifest.md`
4. Log illustration results to workflow_log.md

**Transition to Phase 4:** Illustrations directory populated, `_manifest.md` created

**Skip condition:** If document type doesn't warrant illustrations (rare), skip to Phase 4.

## Phase 4: Research Critic (Review)

**Trigger:** Draft + illustrations are ready

**Actions:**
1. Submit draft, research files, and illustration manifest to Research Critic
2. Critic returns verdict: APPROVED / REVISE / REJECTED
3. Log verdict and full issues table to workflow_log.md

**APPROVED → Phase 5**
**REVISE → Analyst revises, produce draft/v(N+1).md, optionally Illustrator regenerates (if ILLUSTRATION_ISSUES: YES), then resubmit to Critic**
**REJECTED → Back to Phase 1 for additional Scout research, then full cycle repeats**

**Max iterations:** 3. If not approved after 3 → deliver current best with disclaimer.

## Phase 5: Delivery

**Trigger:** APPROVED verdict or max iterations reached

**Actions:**
1. Copy approved draft → `FINAL_REPORT.md`
2. Log completion to workflow_log.md (total time, iterations)
3. Present final document to user with summary of what was produced

## Iteration Rules

- Iteration counter starts at 1 (first Critic review)
- Each REVISE → new draft version (v2, v3)
- Each REJECTED → additional Scout research + new draft
- DO NOT ask user between iterations — proceed automatically
- If same issues persist across 2+ iterations → alert user
