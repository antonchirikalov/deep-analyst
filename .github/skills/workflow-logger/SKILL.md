---
name: workflow-logger
description: "Two-tier logging for multi-agent research workflows: (1) workflow-logger.py for high-level phase tracking in workflow_log.md, (2) agent-trace.py for granular per-step debug tracing in agent_trace.jsonl + agent_trace.md."
---

# Workflow Logger

## Two-Tier Logging System

| Tier | Script | Output | Purpose |
|------|--------|--------|---------|
| **High-level** | `workflow-logger.py` | `workflow_log.md` | Phase transitions, verdicts, completion |
| **Debug trace** | `agent-trace.py` | `agent_trace.jsonl` + `agent_trace.md` | Every agent step: read, write, search, error |

## When to use

### workflow-logger.py (Orchestrator only)
- At workflow start (create log with header)
- At each phase transition
- After each Critic verdict
- At workflow completion (final summary)

### agent-trace.py (ALL agents call this)
- At agent start (`--action start`)
- Before/after each file read (`--action read`)
- After each file write (`--action write --words N`)
- After each search/extract call (`--action search` / `--action extract`)
- On any error (`--action error --status fail`)
- At agent completion (`--action done`)

## How to use

### workflow-logger.py — Initialize log
```bash
python3 .github/skills/workflow-logger/scripts/workflow-logger.py init --folder generated_docs_[TIMESTAMP] --project "Research: [Topic]"
```

### workflow-logger.py — Log parsed parameters (after Phase 0)
```bash
python3 .github/skills/workflow-logger/scripts/workflow-logger.py params --folder generated_docs_[TIMESTAMP] --doc-type "comparison" --size "standard" --max-pages 40 --search-depth "normal" --illustrations "yes" --language "russian"
```

### workflow-logger.py — Log phase start
```bash
python3 .github/skills/workflow-logger/scripts/workflow-logger.py phase --folder generated_docs_[TIMESTAMP] --phase "Phase 1: Retriever (parallel search)" --agents "Retriever x4"
```

### workflow-logger.py — Log event
```bash
python3 .github/skills/workflow-logger/scripts/workflow-logger.py event --folder generated_docs_[TIMESTAMP] --message "Retriever 1 (subtopic_1): done — 8 URLs"
```

### workflow-logger.py — Log Critic verdict
```bash
python3 .github/skills/workflow-logger/scripts/workflow-logger.py verdict --folder generated_docs_[TIMESTAMP] --iteration 1 --verdict REVISE --critical 0 --major 1 --minor 2 --issues '[{"severity":"MAJOR","section":"5","tag":"SOURCE","issue":"Missing citation for claim","action":"Add source URL"}]'
```

### workflow-logger.py — Log completion
```bash
python3 .github/skills/workflow-logger/scripts/workflow-logger.py complete --folder generated_docs_[TIMESTAMP] --iterations 2
```

### agent-trace.py — Log an agent step
```bash
python3 .github/skills/workflow-logger/scripts/agent-trace.py log \
  --folder generated_docs_[TIMESTAMP] \
  --agent Extractor --phase 2 \
  --action extract --status ok \
  --target "https://example.com/article" \
  --detail "Extracted 3200 words" --words 3200
```

### agent-trace.py — Log an error
```bash
python3 .github/skills/workflow-logger/scripts/agent-trace.py log \
  --folder generated_docs_[TIMESTAMP] \
  --agent Extractor --phase 2 \
  --action extract --status fail \
  --target "https://example.com/paywalled" \
  --detail "403 Forbidden"
```

### agent-trace.py — Verify a file exists (inter-phase validation)
```bash
python3 .github/skills/workflow-logger/scripts/agent-trace.py check \
  --folder generated_docs_[TIMESTAMP] \
  --file "research/subtopic_1/_links.md"
# Output: OK: research/subtopic_1/_links.md | 245 words | 12 lines | 1.2 KB
# Exit code 1 if file missing
```

### agent-trace.py — Show trace summary (filter by agent/phase/status)
```bash
python3 .github/skills/workflow-logger/scripts/agent-trace.py summary \
  --folder generated_docs_[TIMESTAMP] \
  [--agent Extractor] [--phase 2] [--status fail]
```

## Actions reference (agent-trace.py)

| Action | When | Typical status |
|--------|------|----------------|
| `start` | Agent begins execution | ok |
| `read` | Reading a file | ok, fail |
| `write` | Writing a file (use --words) | ok, fail |
| `search` | tavily_search, github_search, etc. | ok, warn (few results) |
| `extract` | tavily_extract, fetch_webpage | ok, fail (403, timeout) |
| `validate` | Checking a file format/content | ok, fail |
| `skip` | Intentionally skipping something | skip |
| `error` | Unexpected error | fail |
| `retry` | Retrying a failed operation | ok, fail |
| `generate` | Running external tool (PaperBanana, WeasyPrint) | ok, fail |
| `done` | Agent finished | ok |

## Output files

### workflow_log.md (human-readable, high-level)
```markdown
# Workflow Execution Log
Project: Research: [Topic]
Started: 2026-03-07 14:30:00

## Execution Timeline
### [14:30:01] Phase 1: Retriever (parallel search)
- Activated: Retriever x4
```

### agent_trace.md (human-readable, per-step)
```markdown
# Agent Trace Log

| Time | P | Agent | Action | Target | St | Detail |
|------|---|-------|--------|--------|----|--------|
| 14:30:02 | 1 | Retriever | start | | ✓ | Starting search |
| 14:30:05 | 1 | Retriever | search | tavily: LLM arch | ✓ | Found 8 results |
| 14:30:10 | 2 | Extractor | extract | example.com/paywalled | ✗ | 403 Forbidden |
```

### agent_trace.jsonl (machine-readable, for analysis)
```json
{"ts": "2026-03-07T14:30:02", "agent": "Retriever", "phase": 1, "action": "start", "target": "", "status": "ok", "detail": "Starting search"}
{"ts": "2026-03-07T14:30:10", "agent": "Extractor", "phase": 2, "action": "extract", "target": "https://example.com/paywalled", "status": "fail", "detail": "403 Forbidden"}
```
