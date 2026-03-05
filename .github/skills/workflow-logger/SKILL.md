---
name: workflow-logger
description: Structured markdown logging for multi-agent research workflows. Appends formatted events to workflow_log.md with timestamps, phase info, and agent activity. Use when recording workflow progress, phase transitions, Critic verdicts, or final summaries.
---

# Workflow Logger

## When to use
- At workflow start (create log with header)
- At each phase transition
- After each agent completes work
- After each Research Critic verdict
- At workflow completion (final summary)

## How to use

### Initialize log
```bash
python3 .github/skills/workflow-logger/scripts/workflow-logger.py init --folder generated_docs_[TIMESTAMP] --project "Research: [Topic]"
```

### Log parsed parameters (after Phase 0)
```bash
python3 .github/skills/workflow-logger/scripts/workflow-logger.py params --folder generated_docs_[TIMESTAMP] --doc-type "comparison" --size "standard" --max-pages 40 --search-depth "normal" --illustrations "yes" --language "russian"
```

### Log phase start
```bash
python3 .github/skills/workflow-logger/scripts/workflow-logger.py phase --folder generated_docs_[TIMESTAMP] --phase "Phase 1: Scout (parallel search)" --agents "Scout x4"
```

### Log event
```bash
python3 .github/skills/workflow-logger/scripts/workflow-logger.py event --folder generated_docs_[TIMESTAMP] --message "Scout 1 (subtopic_1): done — 12 facts, 5 sources"
```

### Log Critic verdict
```bash
python3 .github/skills/workflow-logger/scripts/workflow-logger.py verdict --folder generated_docs_[TIMESTAMP] --iteration 1 --verdict REVISE --critical 0 --major 1 --minor 2 --issues '[{"severity":"MAJOR","section":"5","tag":"SOURCE","issue":"Missing citation for claim","action":"Add source URL"}]'
```

If issues JSON is not available, fall back to summary:
```bash
python3 .github/skills/workflow-logger/scripts/workflow-logger.py verdict --folder generated_docs_[TIMESTAMP] --iteration 1 --verdict REVISE --critical 0 --major 1 --minor 2 --summary "Source quality issues and missing citations"
```

### Log completion
```bash
python3 .github/skills/workflow-logger/scripts/workflow-logger.py complete --folder generated_docs_[TIMESTAMP] --iterations 2
```

## Output format
The script appends formatted markdown to `workflow_log.md`:
```markdown
# Workflow Execution Log
Project: Research: [Topic]
Started: 2026-03-05 14:30:00
Status: In Progress

## Execution Timeline

### [14:30:01] Phase 1: Scout (parallel search)
- Activated: Scout x4
- Status: In progress

- [14:30:15] Scout 1 (subtopic_1): done — 12 facts, 5 sources

### [14:31:00] Review - Iteration 1/3
- Verdict: REVISE
- Critical: 0, Major: 1, Minor: 2

## Final Summary
- Status: COMPLETED
- Total iterations: 2
- Processing time: 3m 45s
```
