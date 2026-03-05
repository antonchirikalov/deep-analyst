---
description: File path conventions and artifact folder structure for Deep Analyst research workflow output.
---

# Artifact Management

## Folder Structure

All workflow output goes into a timestamped folder created by Orchestrator at workflow start:

```
generated_docs_[YYYYMMDD_HHMMSS]/
├── workflow_log.md              ← Orchestrator writes after each stage
├── research/
│   ├── subtopic_1.md            ← Scout → raw research data
│   ├── subtopic_2.md            ← Scout → raw research data
│   └── subtopic_N.md            ← Scout → raw research data
├── draft/
│   ├── v1.md                    ← Analyst → first draft
│   ├── v2.md                    ← Analyst → post-revision
│   └── v3.md                    ← Analyst → final version
├── illustrations/
│   ├── _manifest.md             ← Illustrator → diagram metadata
│   ├── diagram_1.png            ← Illustrator → final illustration
│   ├── diagram_1_a.png          ← (temporary) candidate A
│   ├── diagram_1_b.png          ← (temporary) candidate B
│   ├── diagram_1_c.png          ← (temporary) candidate C
│   └── diagram_N.png            ← Illustrator → final illustration
└── FINAL_REPORT.md              ← Final approved document
```

## Rules

- Orchestrator creates the timestamp folder and communicates path to all agents
- ALL agents use the SAME timestamp folder for the workflow run
- Never hardcode absolute paths; always use the provided folder path
- Research files go in: `generated_docs_[TIMESTAMP]/research/`
- Draft versions go in: `generated_docs_[TIMESTAMP]/draft/`
- Illustrations go in: `generated_docs_[TIMESTAMP]/illustrations/`

## File Naming

| Document | Filename |
|----------|----------|
| Workflow Log | `workflow_log.md` |
| Research files | `[subtopic_slug].md` (e.g., `lora_adapters.md`) |
| Draft versions | `v1.md`, `v2.md`, `v3.md` |
| Illustrations | `diagram_N.png` (final), `diagram_N_a.png` (candidate) |
| Illustration manifest | `_manifest.md` |
| Final document | `FINAL_REPORT.md` |

## Candidate Cleanup

Candidate files (`diagram_N_a.png`, `_b.png`, `_c.png`) are temporary. After selection:
- The best candidate is renamed to `diagram_N.png`
- Non-selected candidates may be deleted or kept for audit (default: keep)

## Generated Folder Lifecycle

- Created at workflow start by Orchestrator
- All agents write within this folder only
- After delivery, the folder persists in project root
- Add `generated_docs_*/` to `.gitignore` to exclude from version control
