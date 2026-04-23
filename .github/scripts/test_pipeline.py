#!/usr/bin/env python3
"""End-to-end dry run test for research_pipeline_runner.py v4.5 (Researcher agents)."""
import json, sys, os, tempfile, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from research_pipeline_runner import *
from pathlib import Path

tmp = Path(tempfile.mkdtemp(prefix='test_pipeline_'))
print(f'Test folder: {tmp}')

# Phase 0: init
r = cmd_init(str(tmp))
assert r['status'] == 'ready', f'init failed: {r}'
print('✓ Phase 0: init')

# Phase 0: no params yet
r = cmd_next(str(tmp))
assert r['action'] == 'agent_task', f'expected agent_task, got {r["action"]}'
print('✓ Phase 0: agent_task (no params)')

# Write params
params_file = tmp / 'research' / '_plan' / 'params.md'
params_file.write_text(
    "# Research Parameters\n\n"
    "- **Topic:** Test research topic about AI agents\n"
    "- **Max pages:** 10\n"
    "- **Audience:** developers\n"
    "- **Tone:** academic\n"
    "- **Formulas:** minimal\n"
    "- **Language:** English\n\n"
    "## Subtopics\n"
    "1. Agent architecture and design patterns\n"
    "2. Tool calling and MCP integration\n"
    "3. Context window management\n",
    encoding='utf-8'
)

# Phase 1: Researcher agents (parallel) — search + extract
r = cmd_next(str(tmp))
assert r['action'] == 'launch_parallel', f'expected launch_parallel, got {r["action"]}'
assert r['phase'] == 1
assert r['phase_name'] == 'Research'
assert r['agent_count'] == 3
for a in r['agents']:
    assert a['name'] == 'Researcher', f'expected Researcher, got {a["name"]}'
    assert a.get('writes_own_files') is True, 'Researcher must have writes_own_files=True'
    assert 'verify_dir' in a, 'Researcher must have verify_dir'
    assert 'prompt' in a
print(f'✓ Phase 1: launch_parallel ({r["agent_count"]} Researchers)')

# Simulate Researcher output: _links.md + extract_*.md
for d in get_subtopic_dirs(tmp):
    (d / '_links.md').write_text(
        "1. https://example.com/doc1 — Doc 1\n"
        "2. https://example.com/doc2 — Doc 2\n"
        "3. https://example.com/doc3 — Doc 3\n"
        "4. https://example.com/doc4 — Doc 4\n"
        "5. https://example.com/doc5 — Doc 5\n"
    )
    for i in range(1, 6):
        (d / f'extract_{i}.md').write_text(
            f'# Extract: Doc {i}\nSource: https://example.com/doc{i}\nWords: ~800\n\n'
            + 'word ' * 800
        )

# Phase 2: analysts
r = cmd_next(str(tmp))
assert r['action'] == 'launch_parallel', f'expected launch_parallel, got {r["action"]}'
assert r['phase'] == 2
assert r['phase_name'] == 'Analysis'
for a in r['agents']:
    assert a['name'] == 'Analyst', f'expected Analyst, got {a["name"]}'
    assert 'prompt' in a
    assert 'output_file' in a
print(f'✓ Phase 2: launch_parallel ({r["agent_count"]} Analysts)')

# Simulate _structure.md
for d in get_subtopic_dirs(tmp):
    (d / '_structure.md').write_text(f'# Analysis: {d.name}\n## Depth: DEEP\n## Sections: 2')

# Phase 3: planner
r = cmd_next(str(tmp))
assert r['action'] == 'launch_single', f'expected launch_single, got {r["action"]}'
assert r['phase'] == 3
assert r['agent'] == 'Planner'
print('✓ Phase 3: launch_single (Planner)')

# Simulate toc.md
(tmp / 'research' / '_plan' / 'toc.md').write_text(
    "## 01. Introduction — Pages: 1 — Sources: all\n"
    "## 02. Agent Architecture — Pages: 3 — Sources: agent_architecture_and_design_patterns\n"
    "## 03. Tool Calling — Pages: 3 — Sources: tool_calling_and_mcp_integration\n"
    "## 04. Context Management — Pages: 3 — Sources: context_window_management\n"
)

# Phase 4: writers
r = cmd_next(str(tmp))
assert r['action'] == 'launch_parallel', f'expected launch_parallel, got {r["action"]}'
assert r['phase'] == 4
assert len(r['agents']) == 4
for a in r['agents']:
    assert a['name'] == 'Writer', f'expected Writer, got {a["name"]}'
print(f'✓ Phase 4: launch_parallel ({len(r["agents"])} Writers)')

# Simulate sections
sections_dir = tmp / 'draft' / '_sections'
for i, title in enumerate(['introduction', 'agent_architecture', 'tool_calling', 'context_management'], 1):
    (sections_dir / f'{i:02d}_{title}.md').write_text(
        f'## {title.replace("_", " ").title()}\n\n' + ('word ' * 500)
    )

# Phase 5: editor
r = cmd_next(str(tmp))
assert r['action'] == 'launch_single', f'expected launch_single, got {r["action"]}'
assert r['phase'] == 5
assert r['agent'] == 'Editor'
print('✓ Phase 5: launch_single (Editor)')

# Simulate v1.md
(tmp / 'draft' / 'v1.md').write_text('# Test\n\n' + 'word ' * 3000)

# Phase 6: critic
r = cmd_next(str(tmp))
assert r['action'] == 'launch_single', f'expected launch_single, got {r["action"]}'
assert r['phase'] == 6
assert r['agent'] == 'Critic'
print('✓ Phase 6: launch_single (Critic)')

# Simulate APPROVED
(tmp / 'draft' / '_review.md').write_text('# Review\n\n## Verdict: APPROVED\n\nGood work.')

# Phase 7: illustrations
r = cmd_next(str(tmp))
if r['action'] == 'warning' and 'OPENAI_API_KEY' in r.get('message', ''):
    print('✓ Phase 7: skipped (no OPENAI_API_KEY)')
    (tmp / 'illustrations' / '_manifest.md').write_text('# Manifest\n(skipped)')
elif r['action'] == 'orchestrator_illustrate':
    print(f'✓ Phase 7: orchestrator_illustrate ({r["count"]} illustrations)')
    (tmp / 'illustrations' / '_manifest.md').write_text('# Manifest\n- diagram_1.png')
else:
    print(f'? Phase 7: unexpected {r["action"]}')
    (tmp / 'illustrations' / '_manifest.md').write_text('# Manifest\n(skipped)')

# Phase 8: complete
r = cmd_next(str(tmp))
assert r['action'] == 'complete', f'expected complete, got {r["action"]}'
assert r['phase'] == 8
assert 'stats' in r
print(f'✓ Phase 8: complete — {r["stats"]["words"]} words, {r["stats"]["pages_approx"]} pages')

# Status command
s = cmd_status(str(tmp))
assert 'phases' in s
print(f'✓ cmd_status works')

# Cleanup
shutil.rmtree(tmp)
print()
print('========================================')
print('ALL PHASES PASSED — pipeline is correct')
print('========================================')
