---
description: "Requirements extraction protocol — reads heterogeneous input documents, classifies information, produces a single structured requirements document with traceability."
---

# Requirements Extraction Protocol

## Input Categories

You will process documents of ANY of these types:
- **Briefs** — developer briefs, project descriptions, scope documents
- **Transcripts** — meeting recordings, call transcriptions (often messy, with false starts and tangents)
- **Chats** — Slack/Teams/email threads (informal, implicit context, scattered decisions)
- **Design docs** — solution designs, wireframes descriptions, API specs, ER diagrams
- **Q&A** — stakeholder questions and answers, clarification threads
- **Analysis** — business analysis, market research, competitor analysis

## Processing Rules

### 0. Domain Grounding (BEFORE anything else)
After reading ALL source documents, write ONE sentence answering: "This project is a _____ that does _____".
Every requirement you extract MUST fit this sentence. If during extraction you find yourself writing about a domain NOT matching this sentence — STOP. Delete it. You are hallucinating.

**Example:** If sources describe a "three-party booking marketplace with referral fees" — every FR/NFR must relate to bookings, referrals, businesses, clients, guests. If you write about "portfolio management", "KYC compliance", or "crypto wallets" — those belong to a completely different project and you MUST NOT output them.

### 1. Read ALL documents first
Do NOT start writing after the first document. Read everything, then synthesize.

### 2. FACT vs INFERENCE — strict separation
- **FACT** = directly stated in a source document. Must have a citation: `[Source: {filename}, section/line]`
- **GAP** = something NOT addressed in any document that the architecture would need
- **CONFLICT** = two or more documents say different things. Quote both with citations
- **ASSUMPTION** = reasonable inference where documents are silent. Must be explicitly marked

### 3. Resolve conflicts by source priority
1. Most recent document wins (check dates)
2. Direct stakeholder statement (Q&A, transcript) > written spec
3. Written spec > informal chat
4. If unresolvable → list as CONFLICT in Open Questions

### 4. Extract implicit requirements
Transcripts and chats often contain requirements disguised as:
- "We need to..." / "It should..." / "Can we have..."
- "The problem is..." (implies a requirement to solve it)
- "Like [competitor] does it" (implies a feature reference)
- Numbers mentioned casually ("about 500 users", "within 2 seconds")

### 5. Traceability
Every requirement MUST trace to at least one source document. Format: `[Source: filename.md]`

### 6. File Scope Discipline
- Read ONLY files explicitly listed by the user — no exceptions
- NEVER discover, scan, or browse folders
- NEVER read files that are outputs of other pipelines (`v1.md`, `_review.md`, `_manifest.md`, `generated_*`)
- If `_requirements.md` already exists — IGNORE it entirely, do NOT use it as input

## Output Structure

Write the output as a single markdown document with these sections IN ORDER:

```markdown
# Requirements: {Project Name}
Generated: {date}
Sources analyzed: {N documents listed}

## 1. Stakeholders & Roles
| Role | Description | Source |
|------|-------------|--------|
| {role} | {who they are, what they do in the system} | [Source: file.md] |

## 2. Business Context
{2-3 paragraphs: what the project is, why it exists, business model, revenue streams}
All claims cited.

## 3. Functional Requirements

### FR-{NNN}: {Short title}
- **Priority:** MUST | SHOULD | COULD | WON'T (MoSCoW)
- **Description:** {What the system must do}
- **Acceptance criteria:** {Testable condition}
- **Source:** [Source: file.md, section/quote]

(repeat for each requirement)

### Functional Requirements Summary
| ID | Title | Priority | Source |
|----|-------|----------|--------|

## 4. Non-Functional Requirements

### NFR-{NNN}: {Short title}
- **Category:** Performance | Security | Scalability | Compliance | Reliability | UX
- **Description:** {Measurable requirement}
- **Target metric:** {Specific number or threshold, if stated}
- **Source:** [Source: file.md]

## 5. Business Rules & Constraints
| # | Rule/Constraint | Type | Source |
|---|-----------------|------|--------|
| BR-{N} | {rule} | Business Rule / Technical Constraint / Regulatory | [Source: file.md] |

## 6. Data Model (from sources)
{Only what's EXPLICITLY described in documents — entities, relationships, key fields.
Do NOT invent fields or tables not mentioned in sources.}

## 7. Integration Points
| System | Direction | Protocol | Purpose | Source |
|--------|-----------|----------|---------|--------|
| {external system} | Inbound/Outbound/Both | REST/Webhook/SDK | {why} | [Source: file.md] |

## 8. Open Questions & Conflicts

### Conflicts
| # | Topic | Document A says | Document B says | Resolution needed |
|---|-------|-----------------|-----------------|-------------------|

### Gaps (not addressed in any document)
| # | Topic | Why it matters for architecture |
|---|-------|-------------------------------|

### Assumptions (inferred, not stated)
| # | Assumption | Based on | Risk if wrong |
|---|------------|----------|---------------|
```

## Quality Criteria

The output document is GOOD if:
- Every FR/NFR has a `[Source: ...]` citation
- Conflicts are explicitly listed, not silently resolved by picking one
- Gaps say "not mentioned in any source" — NOT filled with guesses presented as facts
- ASSUMPTION section exists and is non-empty (there are always assumptions)
- No hallucinated requirements — if a document says `wallet_balance` is a decimal field, report that as a FACT, don't add "lacks double-entry ledger" as a requirement unless a source says so
- MoSCoW priorities come from source documents; if not stated, mark as "SHOULD (inferred)"
