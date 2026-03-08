#!/usr/bin/env python3
"""Agent-level debug tracing for the research pipeline.

Every agent calls this script at key steps (start, read, write, search, error, done).
Dual output:
  - agent_trace.jsonl  — machine-readable, one JSON object per line
  - agent_trace.md     — human-readable markdown table

Usage:
  python3 .github/skills/workflow-logger/scripts/agent-trace.py log \
    --folder generated_docs_[TS] \
    --agent Extractor \
    --phase 2 \
    --action read \
    --target "research/subtopic_1/_links.md" \
    --status ok \
    --detail "Found 5 URLs"

  python3 .github/skills/workflow-logger/scripts/agent-trace.py log \
    --folder generated_docs_[TS] \
    --agent Writer \
    --phase 5 \
    --action error \
    --target "draft/_sections/02.md" \
    --status fail \
    --detail "create_file exceeded output limit"

  python3 .github/skills/workflow-logger/scripts/agent-trace.py check \
    --folder generated_docs_[TS] \
    --file "research/subtopic_1/_links.md"

  python3 .github/skills/workflow-logger/scripts/agent-trace.py summary \
    --folder generated_docs_[TS] \
    [--agent Extractor] [--phase 2] [--status fail]

Actions: start, read, write, search, extract, validate, skip, error, retry, done
Statuses: ok, fail, warn, skip
"""

import argparse
import json
import os
import sys
from datetime import datetime


def _ts():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _time():
    return datetime.now().strftime("%H:%M:%S")


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def _jsonl_path(folder: str) -> str:
    return os.path.join(folder, "agent_trace.jsonl")


def _md_path(folder: str) -> str:
    return os.path.join(folder, "agent_trace.md")


# ---------------------------------------------------------------------------
# log command
# ---------------------------------------------------------------------------

STATUS_ICONS = {"ok": "✓", "fail": "✗", "warn": "⚠", "skip": "⊘"}
VALID_ACTIONS = {"start", "read", "write", "search", "extract", "generate",
                 "validate", "skip", "error", "retry", "done"}
VALID_STATUSES = {"ok", "fail", "warn", "skip"}


def cmd_log(args):
    folder = args.folder
    os.makedirs(folder, exist_ok=True)

    action = args.action.lower()
    status = args.status.lower()
    if action not in VALID_ACTIONS:
        print(f"Warning: unknown action '{action}'. Continuing anyway.", file=sys.stderr)
    if status not in VALID_STATUSES:
        print(f"Warning: unknown status '{status}'. Continuing anyway.", file=sys.stderr)

    record = {
        "ts": _ts(),
        "agent": args.agent,
        "phase": args.phase,
        "action": action,
        "target": args.target or "",
        "status": status,
        "detail": args.detail or "",
    }
    if args.words:
        record["words"] = args.words

    # --- JSONL ---
    jsonl = _jsonl_path(folder)
    with open(jsonl, "a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # --- Markdown ---
    md = _md_path(folder)
    icon = STATUS_ICONS.get(status, "?")
    target_short = record["target"]
    if len(target_short) > 50:
        target_short = "…" + target_short[-47:]

    if not os.path.exists(md):
        with open(md, "w") as f:
            f.write("# Agent Trace Log\n\n")
            f.write("| Time | P | Agent | Action | Target | St | Detail |\n")
            f.write("|------|---|-------|--------|--------|----|--------|\n")

    detail_short = (record["detail"][:80] + "…") if len(record["detail"]) > 80 else record["detail"]
    words_suffix = f" ({args.words}w)" if args.words else ""
    line = (f"| {_time()} | {args.phase} | {args.agent} "
            f"| {action} | {target_short}{words_suffix} | {icon} | {detail_short} |\n")

    with open(md, "a") as f:
        f.write(line)

    print(f"[trace] P{args.phase} {args.agent} {action} {icon} {record['target']}")


# ---------------------------------------------------------------------------
# check command — verify file exists, report word count
# ---------------------------------------------------------------------------

def cmd_check(args):
    folder = args.folder
    filepath = os.path.join(folder, args.file)

    if not os.path.exists(filepath):
        print(f"MISSING: {args.file}")
        sys.exit(1)

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    words = len(content.split())
    lines = content.count("\n") + 1
    size_kb = os.path.getsize(filepath) / 1024

    print(f"OK: {args.file} | {words} words | {lines} lines | {size_kb:.1f} KB")


# ---------------------------------------------------------------------------
# summary command — filter and display trace entries
# ---------------------------------------------------------------------------

def cmd_summary(args):
    jsonl = _jsonl_path(args.folder)
    if not os.path.exists(jsonl):
        print("No trace log found.")
        sys.exit(1)

    records = []
    with open(jsonl, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    # Apply filters
    if args.agent:
        records = [r for r in records if r.get("agent", "").lower() == args.agent.lower()]
    if args.phase is not None:
        records = [r for r in records if r.get("phase") == args.phase]
    if args.status:
        records = [r for r in records if r.get("status", "").lower() == args.status.lower()]

    if not records:
        print("No matching trace entries.")
        return

    # Stats
    total = len(records)
    by_status = {}
    by_action = {}
    for r in records:
        s = r.get("status", "?")
        a = r.get("action", "?")
        by_status[s] = by_status.get(s, 0) + 1
        by_action[a] = by_action.get(a, 0) + 1

    print(f"=== Trace Summary ({total} entries) ===")
    print(f"By status: {', '.join(f'{k}={v}' for k, v in sorted(by_status.items()))}")
    print(f"By action: {', '.join(f'{k}={v}' for k, v in sorted(by_action.items()))}")

    # Show errors/failures prominently
    failures = [r for r in records if r.get("status") in ("fail", "warn")]
    if failures:
        print(f"\n--- Failures & Warnings ({len(failures)}) ---")
        for r in failures:
            icon = STATUS_ICONS.get(r["status"], "?")
            print(f"  {icon} [{r['ts']}] P{r['phase']} {r['agent']} "
                  f"{r['action']} {r.get('target', '')} — {r.get('detail', '')}")
    else:
        print("\nNo failures or warnings.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Agent-level debug tracing for the research pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- log ---
    p_log = subparsers.add_parser("log", help="Log an agent action step")
    p_log.add_argument("--folder", required=True, help="Base folder (generated_docs_[TS])")
    p_log.add_argument("--agent", required=True, help="Agent name (Retriever, Extractor, ...)")
    p_log.add_argument("--phase", required=True, type=int, help="Phase number (0-9)")
    p_log.add_argument("--action", required=True,
                        help="Action: start|read|write|search|extract|validate|skip|error|retry|done")
    p_log.add_argument("--target", default="", help="File path or URL being acted upon")
    p_log.add_argument("--status", required=True, help="Status: ok|fail|warn|skip")
    p_log.add_argument("--detail", default="", help="Free-form detail message")
    p_log.add_argument("--words", type=int, default=0, help="Word count (for read/write actions)")
    p_log.set_defaults(func=cmd_log)

    # --- check ---
    p_check = subparsers.add_parser("check", help="Verify file exists and report stats")
    p_check.add_argument("--folder", required=True, help="Base folder (generated_docs_[TS])")
    p_check.add_argument("--file", required=True, help="Relative path within folder to check")
    p_check.set_defaults(func=cmd_check)

    # --- summary ---
    p_summary = subparsers.add_parser("summary", help="Show trace summary with optional filters")
    p_summary.add_argument("--folder", required=True, help="Base folder (generated_docs_[TS])")
    p_summary.add_argument("--agent", default="", help="Filter by agent name")
    p_summary.add_argument("--phase", type=int, default=None, help="Filter by phase number")
    p_summary.add_argument("--status", default="", help="Filter by status (ok|fail|warn|skip)")
    p_summary.set_defaults(func=cmd_summary)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
