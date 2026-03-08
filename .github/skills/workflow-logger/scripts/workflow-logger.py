#!/usr/bin/env python3
"""Structured markdown logger for multi-agent research workflows.

Appends formatted events to workflow_log.md with timestamps.
Adapted for Deep Analyst 5-agent research pipeline.
"""

import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime

logger = logging.getLogger(__name__)


def get_log_path(folder: str) -> str:
    return os.path.join(folder, "workflow_log.md")


def timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def time_only() -> str:
    return datetime.now().strftime("%H:%M:%S")


def append_log(folder: str, content: str) -> None:
    path = get_log_path(folder)
    if not os.path.exists(path):
        logger.error("Log file not found at %s. Run 'init' first.", path)
        sys.exit(1)
    with open(path, "a") as f:
        f.write(content)
    logger.info("Log updated: %s", path)


def cmd_init(args):
    folder = args.folder
    os.makedirs(folder, exist_ok=True)
    path = get_log_path(folder)
    content = f"""# Workflow Execution Log

Project: {args.project}
Started: {timestamp()}
Status: In Progress

## Summary
- Current Phase: Initialization
- Total Iterations: 0
- Status: Starting workflow

## Execution Timeline

"""
    with open(path, "w") as f:
        f.write(content)
    logger.info("Log initialized: %s", path)


def cmd_params(args):
    content = f"""### [{time_only()}] Parameters
- Document type: {args.doc_type}
- Size: {args.size}
- Max pages: {args.max_pages}
- Search depth: {args.search_depth}
- Illustrations: {args.illustrations}
- Language: {args.language}

"""
    append_log(args.folder, content)


def cmd_phase(args):
    content = f"""### [{time_only()}] {args.phase}
- Activated: {args.agents}
- Status: In progress

"""
    append_log(args.folder, content)


def cmd_event(args):
    content = f"""- [{time_only()}] {args.message}

"""
    append_log(args.folder, content)


def cmd_verdict(args):
    content = f"""### [{time_only()}] Review — Iteration {args.iteration}/3
- Verdict: {args.verdict}
- Critical: {args.critical}, Major: {args.major}, Minor: {args.minor}
"""
    if args.illustration_issues:
        content += f"- Illustration Issues: {args.illustration_issues}\n"

    # Parse and render issues table if provided
    if args.issues:
        try:
            issues = json.loads(args.issues)
            if issues:
                content += "\nIssues:\n\n"
                content += "| # | Severity | Section | Tag | Issue | Required Action |\n"
                content += "|---|----------|---------|-----|-------|----------------|\n"
                for i, issue in enumerate(issues, 1):
                    sev = issue.get("severity", "")
                    sec = issue.get("section", "")
                    tag = issue.get("tag", "")
                    desc = issue.get("issue", "")
                    action = issue.get("action", "")
                    content += f"| {i} | {sev} | {sec} | {tag} | {desc} | {action} |\n"
                content += "\n"
        except (json.JSONDecodeError, TypeError):
            content += f"- Key feedback: {args.issues}\n\n"
    elif args.summary:
        content += f"- Key feedback: {args.summary}\n\n"
    else:
        content += "\n"
    append_log(args.folder, content)


def get_started_time(folder: str) -> datetime | None:
    """Extract start time from log file."""
    log_path = get_log_path(folder)
    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            for line in f:
                m = re.search(r"Started:\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})", line)
                if m:
                    try:
                        return datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        pass
    return None


def format_duration(seconds: float) -> str:
    """Format seconds into human-readable duration."""
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}h {m}m {s}s"
    elif m > 0:
        return f"{m}m {s}s"
    else:
        return f"{s}s"


def cmd_complete(args):
    started = get_started_time(args.folder)
    now = datetime.now()
    if started:
        elapsed = (now - started).total_seconds()
        duration_line = f"- Processing time: {format_duration(elapsed)}"
    else:
        duration_line = "- Processing time: unknown (start time not found)"
    content = f"""## Final Summary
- Status: COMPLETED
- Total iterations: {args.iterations}
- Completion time: {timestamp()}
{duration_line}
- Documents approved: YES

"""
    append_log(args.folder, content)
    logger.info("Workflow marked as COMPLETED")


def main():
    parser = argparse.ArgumentParser(description="Workflow markdown logger for Deep Analyst")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init
    p_init = subparsers.add_parser("init", help="Initialize workflow log")
    p_init.add_argument("--folder", required=True, help="Path to generated_docs folder")
    p_init.add_argument("--project", required=True, help="Project name")
    p_init.set_defaults(func=cmd_init)

    # params
    p_params = subparsers.add_parser("params", help="Log parsed workflow parameters")
    p_params.add_argument("--folder", required=True, help="Path to generated_docs folder")
    p_params.add_argument("--doc-type", required=True, help="Document type (comparison, overview, SotA, report)")
    p_params.add_argument("--size", required=True, help="Size preset (brief, standard, detailed)")
    p_params.add_argument("--max-pages", required=True, help="Max pages")
    p_params.add_argument("--search-depth", required=True, help="Search depth (quick, normal, deep)")
    p_params.add_argument("--illustrations", required=True, help="Illustrations (yes, no)")
    p_params.add_argument("--language", required=True, help="Document language")
    p_params.set_defaults(func=cmd_params)

    # phase
    p_phase = subparsers.add_parser("phase", help="Log phase start")
    p_phase.add_argument("--folder", required=True, help="Path to generated_docs folder")
    p_phase.add_argument("--phase", required=True, help="Phase description")
    p_phase.add_argument("--agents", required=True, help="Activated agents")
    p_phase.set_defaults(func=cmd_phase)

    # event
    p_event = subparsers.add_parser("event", help="Log an event")
    p_event.add_argument("--folder", required=True, help="Path to generated_docs folder")
    p_event.add_argument("--message", required=True, help="Event message")
    p_event.set_defaults(func=cmd_event)

    # verdict
    p_verdict = subparsers.add_parser("verdict", help="Log Critic verdict")
    p_verdict.add_argument("--folder", required=True, help="Path to generated_docs folder")
    p_verdict.add_argument("--iteration", required=True, type=int, help="Iteration number")
    p_verdict.add_argument("--verdict", required=True, help="APPROVED|REVISE|REJECTED")
    p_verdict.add_argument("--critical", required=True, type=int, help="Critical issue count")
    p_verdict.add_argument("--major", required=True, type=int, help="Major issue count")
    p_verdict.add_argument("--minor", required=True, type=int, help="Minor issue count")
    p_verdict.add_argument("--illustration-issues", required=False, default="", help="YES or NO")
    p_verdict.add_argument("--summary", required=False, default="", help="Brief feedback summary")
    p_verdict.add_argument("--issues", required=False, default="",
                           help='JSON array of issues: [{"severity":"MAJOR","section":"5","tag":"SOURCE","issue":"desc","action":"fix"}]')
    p_verdict.set_defaults(func=cmd_verdict)

    # complete
    p_complete = subparsers.add_parser("complete", help="Log workflow completion")
    p_complete.add_argument("--folder", required=True, help="Path to generated_docs folder")
    p_complete.add_argument("--iterations", required=True, type=int, help="Total iterations")
    p_complete.set_defaults(func=cmd_complete)

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    args.func(args)


if __name__ == "__main__":
    main()
