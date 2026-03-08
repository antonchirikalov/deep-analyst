#!/usr/bin/env python3
"""Inter-phase validator for the research pipeline.

Validates that each phase produced the expected files in the correct format.
Called by Orchestrator between phases AND manually for debugging.

Usage:
  python3 .github/skills/workflow-logger/scripts/pipeline-validator.py \
    --folder generated_docs_[TS] --phase 0

  python3 .github/skills/workflow-logger/scripts/pipeline-validator.py \
    --folder generated_docs_[TS] --phase all

Exit codes: 0 = all pass, 1 = warnings only, 2 = errors (missing/invalid files)
"""

import argparse
import glob
import os
import re
import sys
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class Check:
    ok: bool
    path: str
    message: str
    severity: str = "error"  # error | warn | info


@dataclass
class PhaseResult:
    phase: int
    checks: list = field(default_factory=list)

    @property
    def errors(self):
        return [c for c in self.checks if not c.ok and c.severity == "error"]

    @property
    def warnings(self):
        return [c for c in self.checks if not c.ok and c.severity == "warn"]

    @property
    def passed(self):
        return [c for c in self.checks if c.ok]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def rel(folder: str, path: str) -> str:
    """Relative path from folder for display."""
    return os.path.relpath(path, folder)


def word_count(path: str) -> int:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return len(f.read().split())


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def file_exists(folder: str, relpath: str, result: PhaseResult,
                severity: str = "error", min_words: int = 1) -> bool:
    """Check file exists and optionally has minimum word count."""
    full = os.path.join(folder, relpath)
    if not os.path.exists(full):
        result.checks.append(Check(False, relpath, "MISSING", severity))
        return False
    wc = word_count(full)
    if wc < min_words:
        result.checks.append(Check(False, relpath,
                                   f"Too short: {wc} words (min {min_words})", severity))
        return False
    result.checks.append(Check(True, relpath, f"exists ({wc} words)"))
    return True


def get_subtopics(folder: str) -> list[str]:
    """Return list of subtopic folder names under research/."""
    research = os.path.join(folder, "research")
    if not os.path.isdir(research):
        return []
    return sorted([
        d for d in os.listdir(research)
        if os.path.isdir(os.path.join(research, d)) and d != "_plan"
    ])


# ---------------------------------------------------------------------------
# Phase validators
# ---------------------------------------------------------------------------

def validate_phase_0(folder: str) -> PhaseResult:
    """Phase 0: Orchestrator → params.md + workflow_log.md"""
    r = PhaseResult(phase=0)

    # params.md
    params_path = os.path.join(folder, "research", "_plan", "params.md")
    if file_exists(folder, "research/_plan/params.md", r, min_words=5):
        text = read_text(params_path)
        # Check required fields
        for field_name in ["max_pages", "language"]:
            if field_name not in text.lower():
                r.checks.append(Check(False, "research/_plan/params.md",
                                      f"Missing field: {field_name}", "warn"))

    # workflow_log.md
    file_exists(folder, "workflow_log.md", r, min_words=5)

    # At least one subtopic folder
    subtopics = get_subtopics(folder)
    if not subtopics:
        r.checks.append(Check(False, "research/",
                               "No subtopic folders found", "warn"))
    else:
        r.checks.append(Check(True, "research/",
                               f"{len(subtopics)} subtopics: {', '.join(subtopics)}"))
    return r


def validate_phase_1(folder: str) -> PhaseResult:
    """Phase 1: Retriever → _links.md per subtopic"""
    r = PhaseResult(phase=1)
    subtopics = get_subtopics(folder)

    if not subtopics:
        r.checks.append(Check(False, "research/", "No subtopic folders", "error"))
        return r

    url_pattern = re.compile(r"^\d+\.\s+https?://", re.MULTILINE)

    for st in subtopics:
        links_rel = f"research/{st}/_links.md"
        links_path = os.path.join(folder, links_rel)
        if not file_exists(folder, links_rel, r, min_words=3):
            continue

        text = read_text(links_path)
        urls = url_pattern.findall(text)
        if len(urls) < 1:
            r.checks.append(Check(False, links_rel,
                                  "No URLs found matching format: '1. https://...'", "error"))
        elif len(urls) < 3:
            r.checks.append(Check(False, links_rel,
                                  f"Only {len(urls)} URLs (<3 minimum)", "warn"))
        else:
            r.checks.append(Check(True, links_rel, f"{len(urls)} URLs"))

        # Check header
        if not text.strip().startswith("# Links:"):
            r.checks.append(Check(False, links_rel,
                                  "Missing header: '# Links: {subtopic}'", "warn"))
    return r


def validate_phase_2(folder: str) -> PhaseResult:
    """Phase 2: Extractor → extract_*.md per subtopic"""
    r = PhaseResult(phase=2)
    subtopics = get_subtopics(folder)

    if not subtopics:
        r.checks.append(Check(False, "research/", "No subtopic folders", "error"))
        return r

    for st in subtopics:
        st_dir = os.path.join(folder, "research", st)
        extracts = sorted(glob.glob(os.path.join(st_dir, "extract_*.md")))

        if not extracts:
            # Check if _links.md existed (subtopic might have been skipped)
            links = os.path.join(st_dir, "_links.md")
            if os.path.exists(links):
                r.checks.append(Check(False, f"research/{st}/extract_*.md",
                                      "No extract files (but _links.md exists)", "error"))
            else:
                r.checks.append(Check(False, f"research/{st}/extract_*.md",
                                      "No extract files (no _links.md either — skipped?)", "warn"))
            continue

        r.checks.append(Check(True, f"research/{st}/",
                               f"{len(extracts)} extracts"))

        for ext in extracts:
            ext_rel = rel(folder, ext)
            text = read_text(ext)
            wc = word_count(ext)

            # Check header format
            if not re.search(r"^# Extract:", text, re.MULTILINE):
                r.checks.append(Check(False, ext_rel,
                                      "Missing header: '# Extract: {title}'", "warn"))
            if not re.search(r"^Source:\s*https?://", text, re.MULTILINE):
                r.checks.append(Check(False, ext_rel,
                                      "Missing 'Source: https://...' line", "warn"))

            if wc < 100:
                r.checks.append(Check(False, ext_rel,
                                      f"Very short extract: {wc} words", "warn"))
            elif wc > 5000:
                r.checks.append(Check(False, ext_rel,
                                      f"Very long extract: {wc} words (chunked write needed?)", "warn"))
    return r


def validate_phase_3(folder: str) -> PhaseResult:
    """Phase 3: Analyst → _structure.md per subtopic"""
    r = PhaseResult(phase=3)
    subtopics = get_subtopics(folder)

    if not subtopics:
        r.checks.append(Check(False, "research/", "No subtopic folders", "error"))
        return r

    depth_pattern = re.compile(r"^## Depth:\s*(DEEP|MEDIUM|SHALLOW|INSUFFICIENT)",
                               re.MULTILINE)

    for st in subtopics:
        struct_rel = f"research/{st}/_structure.md"
        struct_path = os.path.join(folder, struct_rel)

        # Skip subtopics with no extracts
        extracts = glob.glob(os.path.join(folder, "research", st, "extract_*.md"))
        if not extracts:
            r.checks.append(Check(True, struct_rel,
                                  "Skipped (no extracts)", "info"))
            continue

        if not file_exists(folder, struct_rel, r, min_words=20):
            continue

        text = read_text(struct_path)

        # Check header
        if not text.strip().startswith("# Structure:"):
            r.checks.append(Check(False, struct_rel,
                                  "Missing header: '# Structure: {subtopic}'", "warn"))

        # Check depth
        if not depth_pattern.search(text):
            r.checks.append(Check(False, struct_rel,
                                  "Missing '## Depth: DEEP|MEDIUM|SHALLOW|INSUFFICIENT'", "warn"))

        # Check proposed sections
        if "## Proposed sections" not in text:
            r.checks.append(Check(False, struct_rel,
                                  "Missing '## Proposed sections'", "warn"))
    return r


def validate_phase_4(folder: str) -> PhaseResult:
    """Phase 4: Planner → toc.md"""
    r = PhaseResult(phase=4)

    toc_rel = "research/_plan/toc.md"
    toc_path = os.path.join(folder, toc_rel)

    if not file_exists(folder, toc_rel, r, min_words=30):
        return r

    text = read_text(toc_path)

    # Check header
    if not text.strip().startswith("# Table of Contents"):
        r.checks.append(Check(False, toc_rel,
                              "Missing header: '# Table of Contents'", "warn"))

    # Check Total pages
    if not re.search(r"^Total pages:\s*\d+", text, re.MULTILINE):
        r.checks.append(Check(False, toc_rel,
                              "Missing 'Total pages: N'", "warn"))

    # Check sections
    sections = re.findall(r"^## (\d+)\.", text, re.MULTILINE)
    if not sections:
        r.checks.append(Check(False, toc_rel,
                              "No sections found (expected '## 01. Title')", "error"))
    else:
        r.checks.append(Check(True, toc_rel, f"{len(sections)} sections in ToC"))

    # Check each section has Sources and Pages
    section_blocks = re.split(r"^## \d+\.", text, flags=re.MULTILINE)[1:]
    for i, block in enumerate(section_blocks, 1):
        sec_num = f"{i:02d}"
        if not re.search(r"^Pages:\s*\d+", block, re.MULTILINE):
            r.checks.append(Check(False, toc_rel,
                                  f"Section {sec_num}: missing 'Pages:' line", "warn"))
        if not re.search(r"^Sources:\s*\[", block, re.MULTILINE):
            r.checks.append(Check(False, toc_rel,
                                  f"Section {sec_num}: missing 'Sources: [...]'", "warn"))
        # Verify source paths exist
        source_match = re.search(r"^Sources:\s*\[([^\]]+)\]", block, re.MULTILINE)
        if source_match:
            sources = [s.strip() for s in source_match.group(1).split(",")]
            for src in sources:
                src_path = os.path.join(folder, src)
                if not os.path.exists(src_path):
                    r.checks.append(Check(False, toc_rel,
                                          f"Section {sec_num}: source not found: {src}", "error"))
    return r


def validate_phase_5(folder: str) -> PhaseResult:
    """Phase 5: Writer → _sections/NN_*.md"""
    r = PhaseResult(phase=5)

    sections_dir = os.path.join(folder, "draft", "_sections")

    # Get expected sections from toc.md
    toc_path = os.path.join(folder, "research", "_plan", "toc.md")
    if not os.path.exists(toc_path):
        r.checks.append(Check(False, "research/_plan/toc.md",
                              "ToC missing — can't validate section files", "error"))
        return r

    toc_text = read_text(toc_path)
    expected = re.findall(r"^## (\d+)\.", toc_text, re.MULTILINE)

    if not expected:
        r.checks.append(Check(False, "research/_plan/toc.md",
                              "No sections in ToC", "error"))
        return r

    if not os.path.isdir(sections_dir):
        r.checks.append(Check(False, "draft/_sections/",
                              "Directory missing", "error"))
        return r

    section_files = sorted(os.listdir(sections_dir))
    r.checks.append(Check(True, "draft/_sections/",
                           f"{len(section_files)} files"))

    for sec_num in expected:
        # Find file starting with NN
        matching = [f for f in section_files if f.startswith(sec_num)]
        if not matching:
            r.checks.append(Check(False, f"draft/_sections/{sec_num}_*.md",
                                  f"Missing section file for ToC entry #{sec_num}", "error"))
            continue

        sec_file = matching[0]
        sec_rel = f"draft/_sections/{sec_file}"
        sec_path = os.path.join(sections_dir, sec_file)
        wc = word_count(sec_path)

        # Get expected word count from ToC
        sec_block_match = re.search(
            rf"^## {sec_num}\..*?(?=^## \d+\.|\Z)",
            toc_text, re.MULTILINE | re.DOTALL
        )
        expected_words = None
        if sec_block_match:
            words_match = re.search(r"\((\d+)\s*words\)", sec_block_match.group())
            if words_match:
                expected_words = int(words_match.group(1))

        if wc < 50:
            r.checks.append(Check(False, sec_rel,
                                  f"Very short: {wc} words", "error"))
        elif expected_words and abs(wc - expected_words) / expected_words > 0.3:
            r.checks.append(Check(False, sec_rel,
                                  f"{wc} words (expected ~{expected_words}, >30% off)", "warn"))
        else:
            detail = f"{wc} words"
            if expected_words:
                detail += f" (target: {expected_words})"
            r.checks.append(Check(True, sec_rel, detail))
    return r


def validate_phase_6(folder: str) -> PhaseResult:
    """Phase 6: Editor → draft/v1.md"""
    r = PhaseResult(phase=6)

    v1_rel = "draft/v1.md"
    v1_path = os.path.join(folder, v1_rel)

    if not file_exists(folder, v1_rel, r, min_words=100):
        return r

    text = read_text(v1_path)
    wc = word_count(v1_path)

    # Check params for expected size
    params_path = os.path.join(folder, "research", "_plan", "params.md")
    if os.path.exists(params_path):
        params_text = read_text(params_path)
        max_pages_match = re.search(r"max_pages:\s*(\d+)", params_text)
        if max_pages_match:
            max_pages = int(max_pages_match.group(1))
            max_words = max_pages * 300
            min_words = max_words * 0.5
            if wc < min_words:
                r.checks.append(Check(False, v1_rel,
                                      f"Underweight: {wc} words (target: {max_words})", "warn"))
            elif wc > max_words * 1.3:
                r.checks.append(Check(False, v1_rel,
                                      f"Overweight: {wc} words (target: {max_words})", "warn"))
            else:
                r.checks.append(Check(True, v1_rel,
                                      f"Size OK: {wc} words (target: {max_words})"))

    # Check illustration placeholders preserved
    placeholders = re.findall(r"<!-- ILLUSTRATION:", text)
    if placeholders:
        r.checks.append(Check(True, v1_rel,
                               f"{len(placeholders)} illustration placeholders preserved"))
    else:
        r.checks.append(Check(False, v1_rel,
                              "No illustration placeholders found", "warn"))

    # Check has headings (structure)
    headings = re.findall(r"^#{1,3}\s+", text, re.MULTILINE)
    if len(headings) < 3:
        r.checks.append(Check(False, v1_rel,
                              f"Only {len(headings)} headings — document seems unstructured", "warn"))
    return r


def validate_phase_7(folder: str) -> PhaseResult:
    """Phase 7: Critic → draft/_review.md"""
    r = PhaseResult(phase=7)

    review_rel = "draft/_review.md"
    review_path = os.path.join(folder, review_rel)

    if not file_exists(folder, review_rel, r, min_words=10):
        return r

    text = read_text(review_path)

    # Check verdict
    verdict_match = re.search(r"^## Verdict:\s*(APPROVED|REVISE|REJECTED)",
                              text, re.MULTILINE)
    if not verdict_match:
        r.checks.append(Check(False, review_rel,
                              "Missing '## Verdict: APPROVED|REVISE' header", "error"))
    else:
        verdict = verdict_match.group(1)
        r.checks.append(Check(True, review_rel, f"Verdict: {verdict}"))

        if verdict == "REVISE":
            # Check sections to revise list
            revise_lines = re.findall(r"^- section:", text, re.MULTILINE)
            if not revise_lines:
                r.checks.append(Check(False, review_rel,
                                      "REVISE but no '- section:' lines found", "warn"))
            else:
                r.checks.append(Check(True, review_rel,
                                      f"{len(revise_lines)} sections to revise"))
    return r


def validate_phase_8(folder: str) -> PhaseResult:
    """Phase 8: Illustrator → illustrations/*.png + _manifest.md"""
    r = PhaseResult(phase=8)

    illust_dir = os.path.join(folder, "illustrations")

    # v1.md should exist and have img refs (not placeholders)
    v1_path = os.path.join(folder, "draft", "v1.md")
    if os.path.exists(v1_path):
        text = read_text(v1_path)
        remaining = re.findall(r"<!-- ILLUSTRATION:", text)
        img_refs = re.findall(r"!\[.*?\]\(illustrations/", text)

        if remaining:
            r.checks.append(Check(False, "draft/v1.md",
                                  f"{len(remaining)} unresolved illustration placeholders", "error"))
        if img_refs:
            r.checks.append(Check(True, "draft/v1.md",
                                  f"{len(img_refs)} image references"))
        elif not remaining:
            r.checks.append(Check(False, "draft/v1.md",
                                  "No image references and no placeholders", "warn"))

    if not os.path.isdir(illust_dir):
        r.checks.append(Check(False, "illustrations/",
                              "Directory missing", "warn"))
        return r

    pngs = glob.glob(os.path.join(illust_dir, "*.png"))
    if pngs:
        r.checks.append(Check(True, "illustrations/",
                               f"{len(pngs)} PNGs"))
    else:
        r.checks.append(Check(False, "illustrations/",
                              "No PNG files", "warn"))

    # Manifest
    file_exists(folder, "illustrations/_manifest.md", r, severity="warn", min_words=5)

    return r


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

PHASE_VALIDATORS = {
    0: validate_phase_0,
    1: validate_phase_1,
    2: validate_phase_2,
    3: validate_phase_3,
    4: validate_phase_4,
    5: validate_phase_5,
    6: validate_phase_6,
    7: validate_phase_7,
    8: validate_phase_8,
}


def print_result(result: PhaseResult) -> None:
    errors = result.errors
    warnings = result.warnings
    passed = result.passed

    status = "PASS" if not errors else "FAIL"
    warn_str = f", {len(warnings)} warn" if warnings else ""
    print(f"\n{'='*60}")
    print(f"Phase {result.phase}: {status}  "
          f"({len(passed)} pass, {len(errors)} error{warn_str})")
    print(f"{'='*60}")

    for c in result.checks:
        if c.ok:
            icon = "  ✓"
        elif c.severity == "warn":
            icon = "  ⚠"
        else:
            icon = "  ✗"
        print(f"{icon} {c.path} — {c.message}")


def main():
    parser = argparse.ArgumentParser(
        description="Validate pipeline outputs between phases")
    parser.add_argument("--folder", required=True,
                        help="Path to generated_docs_[TIMESTAMP] folder")
    parser.add_argument("--phase", required=True,
                        help="Phase number (0-8) or 'all'")
    args = parser.parse_args()

    folder = args.folder
    if not os.path.isdir(folder):
        print(f"ERROR: folder not found: {folder}")
        sys.exit(2)

    if args.phase == "all":
        phases = sorted(PHASE_VALIDATORS.keys())
    else:
        try:
            phases = [int(args.phase)]
        except ValueError:
            print(f"ERROR: invalid phase: {args.phase}")
            sys.exit(2)

    has_errors = False
    has_warnings = False

    for p in phases:
        if p not in PHASE_VALIDATORS:
            print(f"ERROR: no validator for phase {p}")
            continue
        result = PHASE_VALIDATORS[p](folder)
        print_result(result)
        if result.errors:
            has_errors = True
        if result.warnings:
            has_warnings = True

    # Summary
    print()
    if has_errors:
        print("RESULT: ERRORS FOUND")
        sys.exit(2)
    elif has_warnings:
        print("RESULT: WARNINGS (non-blocking)")
        sys.exit(1)
    else:
        print("RESULT: ALL PASS")
        sys.exit(0)


if __name__ == "__main__":
    main()
