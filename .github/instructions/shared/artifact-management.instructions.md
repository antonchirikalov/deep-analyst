---
description: "Shared artifact management conventions — BASE_FOLDER, folder structure, file naming rules, used by ALL pipeline agents."
applyTo: "**/.github/agents/*.agent.md"
---

# Artifact Management

## BASE_FOLDER Convention

Every sub-agent receives `BASE_FOLDER` in its prompt — the absolute path to `generated_docs_YYYYMMDD_HHMMSS/`.

**All file operations use absolute paths built from BASE_FOLDER:**
```
{BASE_FOLDER}/research/{subtopic_slug}/_links.md
{BASE_FOLDER}/draft/_sections/03_comparison.md
{BASE_FOLDER}/illustrations/_manifest.md
```

**Never use relative paths** in `read_file` or `create_file` calls. Always prepend `BASE_FOLDER`.

## Folder Structure

```
generated_docs_YYYYMMDD_HHMMSS/
├── workflow_log.md            ← Orchestrator (workflow-logger.py)
├── agent_trace.jsonl          ← ALL agents (agent-trace.py, machine-readable)
├── agent_trace.md             ← ALL agents (agent-trace.py, human-readable)
├── research/
│   ├── _plan/
│   │   ├── params.md          ← Orchestrator (Phase 0)
│   │   └── toc.md             ← Planner (Phase 4)
│   ├── {subtopic_slug}/
│   │   ├── _links.md          ← Retriever (Phase 1)
│   │   ├── extract_1.md       ← Extractor (Phase 2)
│   │   ├── extract_2.md       ← Extractor
│   │   ├── extract_N.md       ← Extractor
│   │   └── _structure.md      ← Analyst (Phase 3)
│   └── ... (one folder per subtopic)
├── draft/
│   ├── _sections/
│   │   ├── 01_slug.md         ← Writer (Phase 5)
│   │   ├── 02_slug.md         ← Writer
│   │   └── NN_slug.md         ← Writer
│   ├── v1.md                  ← Editor (Phase 6, always "v1.md")
│   └── _review.md             ← Critic (Phase 7)
└── illustrations/
    ├── _manifest.md           ← Illustrator (Phase 8)
    └── *.png                  ← Illustrator (Phase 8)
```

## File Naming Rules

### Subtopic folders
- Slug format: lowercase, underscores for spaces, ASCII-safe
- Examples: `transformer_architecture`, `security_sandboxing`, `mcp_integrations`
- Created by Orchestrator in Phase 0 decomposition

### Research files
- `_links.md` — always this exact name, one per subtopic folder
- `extract_N.md` — numbered sequentially starting from 1
- `_structure.md` — always this exact name, one per subtopic folder
- Leading underscore (`_`) denotes metadata/index files

### Plan files
- `params.md` — always `research/_plan/params.md`
- `toc.md` — always `research/_plan/toc.md`

### Draft files
- Section files: `NN_slug.md` where NN is zero-padded (01, 02, ..., 30)
- Slug derived from ToC section title: lowercase, underscores, ASCII
- Merged document: always `draft/v1.md` (overwritten on revision, no v2/v3)
- Review: always `draft/_review.md` (overwritten on each Critic pass)

### Illustration files
- `_manifest.md` — index of all generated illustrations
- Image files: named by Illustrator based on section and description

### Log files
- `workflow_log.md` — Orchestrator only, via workflow-logger.py
- `agent_trace.jsonl` — ALL agents, via agent-trace.py, appended
- `agent_trace.md` — ALL agents, via agent-trace.py, appended

## Path Construction Examples

Given `BASE_FOLDER = /Users/user/project/generated_docs_20260307_143000/`:

| Agent | Operation | Absolute path |
|---|---|---|
| Retriever | Write links | `{BASE_FOLDER}/research/transformer_arch/_links.md` |
| Extractor | Write extract | `{BASE_FOLDER}/research/transformer_arch/extract_1.md` |
| Analyst | Read extracts | `{BASE_FOLDER}/research/transformer_arch/extract_*.md` (list_dir then read) |
| Analyst | Write structure | `{BASE_FOLDER}/research/transformer_arch/_structure.md` |
| Planner | Read all structures | `{BASE_FOLDER}/research/*/` (list_dir each) |
| Planner | Write ToC | `{BASE_FOLDER}/research/_plan/toc.md` |
| Writer | Read sources | paths from toc.md, prepend BASE_FOLDER |
| Writer | Write section | `{BASE_FOLDER}/draft/_sections/02_architecture.md` |
| Editor | Read all sections | `{BASE_FOLDER}/draft/_sections/` (list_dir) |
| Editor | Write merged | `{BASE_FOLDER}/draft/v1.md` |
| Critic | Read merged | `{BASE_FOLDER}/draft/v1.md` |
| Critic | Write review | `{BASE_FOLDER}/draft/_review.md` |
| Illustrator | Read merged | `{BASE_FOLDER}/draft/v1.md` |
| Illustrator | Write images | `{BASE_FOLDER}/illustrations/` |

## Overwrite Policy

| File | On revision |
|---|---|
| `_links.md` | Never overwritten (Phase 1 runs once) |
| `extract_N.md` | Never overwritten |
| `_structure.md` | Never overwritten (Phase 3 runs once) |
| `toc.md` | Never overwritten (Phase 4 runs once) |
| `NN_slug.md` sections | Overwritten by Writer on revision |
| `v1.md` | Overwritten by Editor on revision |
| `_review.md` | Overwritten by Critic on each pass |
| `_manifest.md` | Created once in Phase 8 |

## Validation

Use `agent-trace.py check` to verify file existence and minimum word count:
```bash
python3 .github/skills/workflow-logger/scripts/agent-trace.py check \
  --folder $BASE_FOLDER --file "research/{subtopic}/_links.md"
```

This returns exit code 0 if file exists and has content, non-zero otherwise.
