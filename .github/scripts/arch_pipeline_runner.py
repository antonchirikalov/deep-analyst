#!/usr/bin/env python3
"""
Deterministic Pipeline Runner for architecture analysis pipeline.

Imports shared helpers from research_pipeline_runner.py. Implements arch-specific
phases: Source Analysis → Assessment → Proposals → Planning → Writing →
Editing → Review → Illustration.

Usage:
    python3 .github/scripts/arch_pipeline_runner.py init [base_folder]
    python3 .github/scripts/arch_pipeline_runner.py next <base_folder>
    python3 .github/scripts/arch_pipeline_runner.py status <base_folder>
"""

import json
import signal
import sys
import re
import os
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# ═══════════════════════════════════════════════════════════════
# VENV BOOTSTRAP — auto-activate .venv when run outside of it
# ═══════════════════════════════════════════════════════════════

_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent.parent
_VENV_DIR = _PROJECT_ROOT / ".venv"
_VENV_PYTHON = _VENV_DIR / (Path("Scripts") / "python.exe" if os.name == "nt" else Path("bin") / "python3")
_REQUIREMENTS = ["loguru"]


def _bootstrap_venv():
    """Re-exec under .venv/bin/python3 if running with system Python.
    Creates the venv and installs dependencies if it doesn't exist."""
    if sys.prefix != sys.base_prefix:
        return  # already in a venv
    if not _VENV_DIR.exists():
        print(f"[bootstrap] Creating {_VENV_DIR} ...", file=sys.stderr)
        subprocess.check_call([sys.executable, "-m", "venv", str(_VENV_DIR)])
        subprocess.check_call(
            [str(_VENV_PYTHON), "-m", "pip", "install", "-q"] + _REQUIREMENTS
        )
    elif not _VENV_PYTHON.exists():
        print(f"[bootstrap] ERROR: {_VENV_PYTHON} not found", file=sys.stderr)
        sys.exit(1)
    print(f"[bootstrap] Re-launching with {_VENV_PYTHON}", file=sys.stderr)
    os.execv(str(_VENV_PYTHON), [str(_VENV_PYTHON)] + sys.argv)


_bootstrap_venv()

from loguru import logger

# Import shared helpers from research pipeline
from research_pipeline_runner import (
    slugify,
    word_count,
    parse_toc_sections,
    parse_verdict,
    parse_verdict_details,
    find_section_file,
    load_retries,
    save_retries,
    can_retry,
    revision_count,
)

# ═══════════════════════════════════════════════════════════════
# LOGGING  (loguru: stderr=INFO, file=DEBUG with rotation)
# ═══════════════════════════════════════════════════════════════

# research_pipeline_runner already configured stderr sink on import;
# we only need the file sink per base folder.
from research_pipeline_runner import _file_sinks


def _setup_file_log(base: Path):
    """Add file sink to log DEBUG-level trace into BASE_FOLDER/pipeline.log."""
    log_file = str(base / "pipeline.log")
    if log_file not in _file_sinks:
        sid = logger.add(
            log_file,
            level="DEBUG",
            format="{time:HH:mm:ss.SSS} [{level.name:<7}] {function}:{line} | {message}",
            rotation="5 MB",
            retention=3,
            encoding="utf-8",
        )
        _file_sinks[log_file] = sid


# ═══════════════════════════════════════════════════════════════
# ARCH-SPECIFIC HELPERS
# ═══════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════
# STATE PERSISTENCE — eliminates full re-scan on every cmd_next()
# ═══════════════════════════════════════════════════════════════

def load_state(base: Path) -> dict:
    """Load pipeline state from _state.json. Returns empty dict if not found."""
    state_file = base / "_state.json"
    if state_file.exists():
        try:
            return json.loads(state_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            logger.warning("Corrupt _state.json — resetting")
    return {}


def save_state(base: Path, state: dict):
    """Persist pipeline state to _state.json."""
    state["updated_at"] = datetime.now().isoformat()
    (base / "_state.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def mark_phase_done(base: Path, phase, **extra):
    """Mark a phase as completed in state. Extra kwargs are merged into state."""
    state = load_state(base)
    completed = state.get("completed_phases", [])
    if phase not in completed:
        completed.append(phase)
    state["completed_phases"] = completed
    state["current_phase"] = phase
    state.update(extra)
    save_state(base, state)


def get_source_dirs(base: Path) -> list:
    """Return sorted list of source area directories (excluding _plan)."""
    research = base / "research"
    if not research.exists():
        return []
    return sorted([
        d for d in research.iterdir()
        if d.is_dir() and d.name != "_plan"
    ])


def parse_arch_params(base: Path) -> dict:
    """Parse architecture-specific params.md with ## Sources section."""
    params_file = base / "research" / "_plan" / "params.md"
    if not params_file.exists():
        return {}
    text = params_file.read_text(encoding="utf-8")
    params = {}

    # Parse key-value pairs: - **Key:** Value  or  - **Key**: Value
    for line in text.splitlines():
        m = re.match(r"-\s+\*\*(.+?):?\*\*:?\s*(.+)", line)
        if m:
            key = m.group(1).strip().lower()
            val = m.group(2).strip()
            params[key] = val
            # Parse max_pages as int immediately to avoid applying regex to int
            if key in ("max pages", "max_pages"):
                m2 = re.search(r"(\d+)", val)
                if m2:
                    params["max_pages"] = int(m2.group(1))
                break

    # Ensure max_pages is int
    for key in ("max pages", "max_pages"):
        if key in params and isinstance(params[key], str):
            m2 = re.search(r"(\d+)", params[key])
            if m2:
                params["max_pages"] = int(m2.group(1))
                break

    params["topic"] = params.get("topic", params.get("тема", "Architecture"))
    params["mode"] = params.get("mode", "architecture")

    # Parse ## Sources section
    sources = []
    in_sources = False
    for line in text.splitlines():
        if re.search(r"##\s*Sources", line, re.IGNORECASE):
            in_sources = True
            continue
        if in_sources:
            if line.strip().startswith("#"):
                break
            m_src = re.match(
                r"\s*\d+\.\s+(.+?)\s*[—–-]\s*(?:path|query|confluence):\s*(.+?)\s*[—–-]\s*type:\s*(\w+)",
                line,
                re.IGNORECASE,
            )
            if m_src:
                name = m_src.group(1).strip()
                location = m_src.group(2).strip()
                stype = m_src.group(3).strip().lower()
                source = {"name": name, "type": stype}
                if stype in ("code", "docs", "config"):
                    source["path"] = location
                elif stype == "web":
                    source["query"] = location.strip('"').strip("'")
                elif stype == "confluence":
                    # Parse space=X, title=Y
                    sm = re.search(r"space=(\S+)", location)
                    tm = re.search(r"title=(.+?)(?:,|$)", location)
                    if sm:
                        source["space"] = sm.group(1)
                    if tm:
                        source["title"] = tm.group(1).strip()
                sources.append(source)

    params["sources"] = sources
    return params


# ═══════════════════════════════════════════════════════════════
# PROMPT BUILDERS — sub-agents READ files, RETURN text
# Orchestrator writes the returned text to output_file
# ═══════════════════════════════════════════════════════════════

def prompt_source_analyzer(base: Path, source: dict, area_slug: str) -> str:
    stype = source["type"]
    path = source.get("path", "N/A")
    name = source["name"]

    type_instructions = {
        "code": (
            f"Analyze the code at: {path}\n"
            "Focus on:\n"
            "- Module/package structure (entry points, core modules, utilities)\n"
            "- Class/function hierarchy and dependencies\n"
            "- API surface (public interfaces, endpoints, exports)\n"
            "- Patterns used (MVC, hexagonal, event-driven, etc.)\n"
            "- Key configuration and environment dependencies\n"
            "- Error handling and logging patterns\n"
        ),
        "docs": (
            f"Analyze documentation at: {path}\n"
            "Focus on:\n"
            "- Architecture decisions (ADRs, RFCs)\n"
            "- Requirements and constraints\n"
            "- System boundaries and integration points\n"
            "- Non-functional requirements (performance, security, scalability)\n"
            "- Known limitations or tech debt\n"
        ),
        "config": (
            f"Analyze configuration files at: {path}\n"
            "Focus on:\n"
            "- Infrastructure topology (services, ports, networks)\n"
            "- Environment variables and secrets management\n"
            "- Build and deployment pipeline\n"
            "- Dependencies and version constraints\n"
            "- Resource limits and scaling configuration\n"
        ),
    }

    return (
        f'You are a Source Analyzer. Analyze source area "{name}" (type: {stype}).\n\n'
        f'{type_instructions.get(stype, f"Analyze files at: {path}")}\n\n'
        f"Extract comprehensive architecture-relevant information.\n"
        f"Target: 1000-3000 words per extract file.\n"
        f"Max 50 files to read.\n"
        f"Skip: node_modules/, .git/, __pycache__/, venv/, .venv/, dist/, build/\n\n"
        f"RETURN your analysis as markdown. Start directly with content.\n"
        f"Include specific file paths, class names, function signatures."
    )


def prompt_assessor(base: Path, area_slug: str, main_topic: str) -> str:
    return (
        f'You are an Architecture Assessor. Assess area "{area_slug.replace("_", " ")}".\n'
        f'Overall topic: "{main_topic}"\n\n'
        f"Read ALL extract_*.md files in: {base}/research/{area_slug}/\n\n"
        f"YOUR TASK:\n"
        f"1. Identify architecture patterns found (with evidence from specific files)\n"
        f"2. Identify anti-patterns and tech debt (severity: HIGH/MEDIUM/LOW)\n"
        f"3. Map dependencies (internal and external)\n"
        f"4. List pain points and their impact\n"
        f"5. Propose improvement opportunities\n"
        f"6. Add cross-references to other areas if relevant\n"
        f"7. Rate depth: DEEP / MEDIUM / SHALLOW\n\n"
        f"RETURN your assessment as markdown. Start with # Assessment: {{area_name}}"
    )


def prompt_solution_architect(base: Path) -> str:
    return (
        f"You are the Solution Architect. Design 2-3 architecture proposals.\n\n"
        f"Read these files:\n"
        f"- {base}/research/_plan/params.md (problem, constraints, output format)\n"
        f"- All {base}/research/*/_assessment.md files\n"
        f"- If no _assessment.md files exist, read extract_*.md files directly\n\n"
        f"YOUR TASK:\n"
        f"1. Summarize the Current State from assessments\n"
        f"2. Define the Problem Statement clearly\n"
        f"3. Propose 2-3 DISTINCT architecture options. For each:\n"
        f"   - Architecture description with component diagram\n"
        f"   - Pros (concrete, evidence-based)\n"
        f"   - Cons (honest, not sugar-coated)\n"
        f"   - Risk Assessment (technical + organizational)\n"
        f"5. Include <!-- ILLUSTRATION --> placeholders for architecture diagrams\n\n"
        f"NOTE: Do NOT include effort estimates, timelines, or migration roadmaps "
        f"unless the user explicitly requested them in the original prompt.\n\n"
        f"RETURN as markdown. Start with # Architecture Proposals"
    )


def prompt_arch_planner(base: Path) -> str:
    return (
        f"You are a document Planner. Build a unified Table of Contents for an "
        f"architecture proposal document.\n\n"
        f"Read these files:\n"
        f"- {base}/research/_plan/params.md (topic, max_pages, audience, language)\n"
        f"- {base}/research/_plan/_proposals.md (architecture proposals)\n"
        f"- All {base}/research/*/_assessment.md files (area assessments)\n\n"
        f"The document structure MUST include:\n"
        f"- Executive Summary\n"
        f"- Current State Analysis (from assessments)\n"
        f"- Problem Statement\n"
        f"- Architecture Options (one section per option from _proposals.md)\n"
        f"- Comparison Matrix\n"
        f"- Recommendation\n"
        f"- Risk Registry\n"
        f"- Appendices (glossary, references)\n\n"
        f"FORMAT (MANDATORY — pipeline parses with regex):\n"
        f"## NN. Section Title — Pages: N — Sources: file1, file2\n\n"
        f"Example:\n"
        f"## 01. Executive Summary — Pages: 2 — Sources: _proposals.md, all\n"
        f"## 02. Current State — Pages: 3 — Sources: _assessment.md files\n\n"
        f"Total pages MUST match max_pages from params.md (+-1).\n"
        f"1 page = 300 words.\n\n"
        f"RETURN the ToC as markdown. Start directly with content."
    )


def prompt_arch_writer(base: Path, section: dict, is_revision: bool = False) -> str:
    words = section["words"]
    revision_note = ""
    if is_revision:
        reviews = sorted(base.glob("draft/_review_v*.md"))
        if reviews:
            revision_note = (
                f"\n\nREVISION MODE: Read {reviews[-1]} for Critic feedback. "
                f"Address ALL feedback. Revision #{len(reviews)}."
            )

    return (
        f"You are a technical Writer. Write one section of an architecture proposal.\n\n"
        f'Section: {section["num"]}. {section["title"]}\n'
        f'Page budget: {section["pages"]} pages ({words} words MINIMUM)\n\n'
        f"Read these files:\n"
        f"- {base}/research/_plan/params.md (language, audience, tone)\n"
        f"- {base}/research/_plan/_proposals.md (architecture proposals)\n"
        f"- Assessment files: {base}/research/*/_assessment.md\n"
        f'- Source extracts for: {section["sources"]} '
        f"(read extract_*.md files in those folders under {base}/research/)\n"
        f"{revision_note}\n\n"
        f"MANDATORY RULES:\n"
        f"1. WORD COUNT: Section MUST be {words} words ± 15%. "
        f"Going OVER budget is a FAILURE — cut ruthlessly. "
        f"Target range: {int(words * 0.85)}-{int(words * 1.15)} words.\n"
        f"2. TECHNICAL DEPTH: Include ALL technical details — component names, "
        f"API endpoints, config parameters, dependency versions. Copy VERBATIM.\n"
        f"3. ILLUSTRATION PLACEHOLDERS: At least 1 per 2+ page section:\n"
        f'   <!-- ILLUSTRATION: type="architecture|comparison|pipeline", '
        f'section="{section["num"]}. {section["title"]}", '
        f'description="Detailed description of visualization" -->\n'
        f'   Follow EVERY placeholder with a caption: *Fig. N. Short caption*\n'
        f'4. NO FILLER: Ban "мощный", "инновационный", "comprehensive", "революционный".\n'
        f"5. NO ASCII DIAGRAMS: NEVER use box-drawing characters. "
        f"Use only <!-- ILLUSTRATION: ... --> placeholders for diagrams.\n"
        f"6. TRADE-OFFS: Every option MUST have honest pros AND cons.\n"
        f"7. LANGUAGE: Write in the language from params.md.\n"
        f"8. NO TIMELINES: Do NOT include effort estimates, implementation timelines, "
        f"sprint plans, or schedules unless explicitly requested in prompts.\n\n"
        f"RETURN the section as markdown starting with ## heading. No preamble."
    )


def prompt_arch_editor(base: Path) -> str:
    return (
        f"You are a document Editor. Merge all sections into one cohesive "
        f"architecture proposal document.\n\n"
        f"Read these files:\n"
        f"- {base}/research/_plan/toc.md (section order)\n"
        f"- {base}/research/_plan/params.md (language, title)\n"
        f"- All files in {base}/draft/_sections/ (in NN_ order)\n\n"
        f"RULES:\n"
        f"- Maintain ToC order (01, 02, 03...)\n"
        f"- Add # title and executive summary at top\n"
        f"- Add transitions between sections\n"
        f"- Remove duplicated content (keep fullest version)\n"
        f"- Preserve ALL <!-- ILLUSTRATION: ... --> placeholders\n"
        f"- REMOVE any ASCII/box-drawing diagrams. Replace with "
        f"<!-- ILLUSTRATION: ... --> placeholder or plain text list.\n"
        f"- Ensure comparison matrix is a proper markdown table\n"
        f"- Do NOT reduce word count\n\n"
        f"RETURN the merged document as markdown. Start with # title."
    )


def prompt_arch_critic(base: Path, max_pages: int) -> str:
    min_words = int(max_pages * 300 * 0.8)
    max_words = int(max_pages * 300 * 1.15)
    return (
        f"You are a document Critic. Review an architecture proposal.\n\n"
        f"Read these files:\n"
        f"- {base}/draft/v1.md (draft)\n"
        f"- {base}/research/_plan/params.md (parameters)\n"
        f"- {base}/research/_plan/toc.md (page budgets)\n"
        f"- {base}/research/_plan/_proposals.md (original proposals)\n\n"
        f"CRITICAL RULES:\n"
        f"1. Word budget: target {max_pages * 300} words (range {min_words}-{max_words}).\n"
        f"   - If UNDER {min_words} words -> REVISE (too thin).\n"
        f"   - If OVER {max_words} words -> REVISE (cut bloat).\n"
        f"2. ARCHITECTURE-SPECIFIC checks:\n"
        f"   - Each option MUST have clear trade-offs (not just positives)\n"
        f"   - Risk assessment MUST be concrete (not generic)\n"
        f"   - Migration path MUST have actionable steps\n"
        f"   - Comparison matrix MUST use consistent criteria\n"
        f"   - Recommendation MUST cite evidence from assessments\n"
        f"3. Check filler language (\"мощный\", \"comprehensive\" without substance).\n"
        f"4. Check section word counts vs ToC budgets (± 15%). Sections OVER budget -> REVISE.\n"
        f"5. Check for duplicated content.\n"
        f"6. ASCII DIAGRAMS: If box-drawing characters found -> REVISE.\n\n"
        f"OUTPUT FORMAT (MANDATORY — pipeline parses JSON block):\n"
        f"Write your review as markdown, then at the END include this EXACT block:\n\n"
        f"```json\n"
        f'{{"verdict": "APPROVED" or "REVISE", "issues": ["issue1", ...], "section_targets": ["03", "07", ...]}}\n'
        f"```\n\n"
        f"If APPROVED, issues and section_targets can be empty arrays.\n"
        f"If REVISE, list the specific sections that need work.\n\n"
        f"RETURN your review as markdown. No preamble."
    )


# ═══════════════════════════════════════════════════════════════
# COMMANDS
# ═══════════════════════════════════════════════════════════════

def cmd_init(base_folder: str) -> dict:
    base = Path(base_folder).resolve()
    (base / "research" / "_plan").mkdir(parents=True, exist_ok=True)
    (base / "draft" / "_sections").mkdir(parents=True, exist_ok=True)
    (base / "illustrations").mkdir(parents=True, exist_ok=True)
    _setup_file_log(base)
    logger.info("INIT arch pipeline: {}", base)
    return {
        "status": "ready",
        "folder": str(base),
        "pipeline": "architecture",
        "next_step": "Write research/_plan/params.md with ## Sources, then run next",
    }


def cmd_next(base_folder: str) -> dict:
    base = Path(base_folder).resolve()
    if not base.exists():
        return {"action": "error", "message": f"Folder {base} does not exist."}

    _setup_file_log(base)
    params = parse_arch_params(base)
    retries = load_retries(base)
    state = load_state(base)
    if retries:
        logger.debug("Retry state: {}", retries)
    if state:
        logger.debug("Pipeline state: phase={}, completed={}",
                     state.get("current_phase"), state.get("completed_phases", []))

    # ── Phase 0: Decomposition ──
    if not params or not params.get("sources"):
        logger.info("Phase 0: params or sources not found — need decomposition")
        return {
            "action": "agent_task",
            "phase": 0,
            "phase_name": "Decomposition",
            "message": (
                "Write research/_plan/params.md with Topic, Max pages, "
                "and ## Sources section listing code/docs/config/web/confluence sources."
            ),
        }

    main_topic = params.get("topic", "Architecture")
    max_pages = params.get("max_pages", 20)
    sources = params["sources"]
    logger.info("Params: topic={!r}, max_pages={}, sources={} (types: {})",
                main_topic, max_pages, len(sources),
                {s['type'] for s in sources})

    # Create area folders for file-based sources
    for src in sources:
        if src["type"] in ("code", "docs", "config"):
            slug = slugify(src["name"])
            (base / "research" / slug).mkdir(parents=True, exist_ok=True)

    # Also create folders for web/confluence sources
    for src in sources:
        if src["type"] in ("web", "confluence"):
            slug = slugify(src["name"])
            (base / "research" / slug).mkdir(parents=True, exist_ok=True)

    source_dirs = get_source_dirs(base)

    # Classify sources by handler
    web_sources = [s for s in sources if s["type"] == "web"]
    confluence_sources = [s for s in sources if s["type"] == "confluence"]
    file_sources = [s for s in sources if s["type"] in ("code", "docs", "config")]

    # ═══════════ Phase 1a: Web Research — ORCHESTRATOR searches ═══════════
    web_missing = []
    for src in web_sources:
        slug = slugify(src["name"])
        area_dir = base / "research" / slug
        if not list(area_dir.glob("extract_*.md")):
            web_missing.append(src)

    if web_missing:
        logger.info("Phase 1a: {} web sources need research: {}",
                    len(web_missing), ", ".join(s['name'] for s in web_missing))
        searches = []
        for src in web_missing:
            slug = slugify(src["name"])
            query = src.get("query", src["name"])
            searches.append({
                "query": f"{query} architecture implementation internals",
                "query_alt": f"{query} design patterns best practices comparison",
                "source_name": src["name"],
                "source_slug": slug,
                "output_dir": str((base / "research" / slug).relative_to(base)),
            })
        return {
            "action": "orchestrator_web_research",
            "phase": 1,
            "phase_name": "Web Research",
            "count": len(searches),
            "sources": searches,
            "instructions": (
                "For EACH source:\n"
                "1. Use fetch_webpage on known documentation URLs for the topic, "
                "or search your knowledge for relevant URLs.\n"
                "2. Extract FULL content from each URL.\n"
                "3. Write each extract to: {output_dir}/extract_N.md\n"
                "   Header: # Extract: [title]\\nSource: [url]\\nWords: ~N\\n\\n[content]\n"
                "4. Aim for 3-5 extracts per source, 1000+ words each.\n"
                "Skip failed URLs."
            ),
        }

    # ═══════════ Phase 1b: Confluence — ORCHESTRATOR reads ═══════════
    confluence_missing = []
    for src in confluence_sources:
        slug = slugify(src["name"])
        area_dir = base / "research" / slug
        if not list(area_dir.glob("extract_*.md")):
            confluence_missing.append(src)

    if confluence_missing:
        logger.info("Phase 1b: {} Confluence sources need extraction: {}",
                    len(confluence_missing), ", ".join(s['name'] for s in confluence_missing))
        conf_tasks = []
        for src in confluence_missing:
            slug = slugify(src["name"])
            conf_tasks.append({
                "source_name": src["name"],
                "source_slug": slug,
                "space": src.get("space", ""),
                "title": src.get("title", ""),
                "output_file": str(
                    (base / "research" / slug / "extract_1.md").relative_to(base)
                ),
            })
        return {
            "action": "orchestrator_confluence",
            "phase": 1,
            "phase_name": "Confluence Extraction",
            "count": len(conf_tasks),
            "sources": conf_tasks,
            "instructions": (
                "For EACH source:\n"
                "1. Call mcp_mcp-atlassian_confluence_get_page(space, title) "
                "or confluence_search.\n"
                "2. Write FULL page content to output_file.\n"
                "3. Include child pages if relevant.\n"
                "Header: # Extract: [page_title]\\nSource: confluence/{space}/{title}\\n"
                "Words: ~N\\n\\n[content]"
            ),
        }

    # ═══════════ Phase 1c: File Analysis — sub-agents scan code/docs/config ═══════════
    file_missing = []
    for src in file_sources:
        slug = slugify(src["name"])
        area_dir = base / "research" / slug
        if not list(area_dir.glob("extract_*.md")):
            file_missing.append(src)

    if file_missing:
        logger.info("Phase 1c: {} file sources to analyze: {}",
                    len(file_missing),
                    ", ".join(f"{s['name']}({s['type']})" for s in file_missing))
        agents = []
        for src in file_missing:
            slug = slugify(src["name"])
            agents.append({
                "name": "Source Analyzer",
                "prompt": prompt_source_analyzer(base, src, slug),
                "output_file": str(
                    (base / "research" / slug / "extract_1.md").relative_to(base)
                ),
                "description": f"Analyze {src['type']}: {src['name']}",
            })
        return {
            "action": "launch_parallel",
            "phase": 1,
            "phase_name": "Source Analysis",
            "agent_count": len(agents),
            "agents": agents,
        }

    # ── Validate Phase 1 ──
    weak_areas = []
    for d in source_dirs:
        exts = list(d.glob("extract_*.md"))
        real = [e for e in exts if word_count(e) > 50]
        logger.debug("Phase 1 validate: {} — extracts={} (real={})", d.name, len(exts), len(real))
        if len(real) < 1:
            weak_areas.append({"area": d.name, "extracts": len(real)})

    if weak_areas:
        logger.warning("Phase 1 weak areas: {}",
                       ", ".join(f"{wa['area']}(exts={wa['extracts']})" for wa in weak_areas))
    else:
        mark_phase_done(base, 1)
    if weak_areas and can_retry(base, "phase_1_quality"):
        # Re-trigger based on source type
        for wa in weak_areas:
            matched = next(
                (s for s in sources if slugify(s["name"]) == wa["area"]), None
            )
            if matched and matched["type"] in ("code", "docs", "config"):
                return {
                    "action": "launch_parallel",
                    "phase": 1,
                    "phase_name": "Source Analysis (retry)",
                    "agent_count": 1,
                    "agents": [
                        {
                            "name": "Source Analyzer",
                            "prompt": prompt_source_analyzer(
                                base, matched, wa["area"]
                            )
                            + "\nRETRY: Previous extraction was empty or too short.",
                            "output_file": str(
                                (
                                    base / "research" / wa["area"] / "extract_1.md"
                                ).relative_to(base)
                            ),
                            "description": f"Retry analyze {matched['name']}",
                        }
                    ],
                }

    # ═══════════ Phase 2: Assessment — sub-agents assess each area ═══════════
    areas_with_extracts = [
        d for d in source_dirs if list(d.glob("extract_*.md"))
    ]
    missing_assessments = [
        d for d in areas_with_extracts if not (d / "_assessment.md").exists()
    ]

    if not missing_assessments:
        mark_phase_done(base, 2)

    if missing_assessments:
        logger.info("Phase 2: {} areas need assessment: {}",
                    len(missing_assessments), ", ".join(d.name for d in missing_assessments))
        agents = []
        for d in missing_assessments:
            agents.append({
                "name": "Arch Assessor",
                "prompt": prompt_assessor(base, d.name, main_topic),
                "output_file": str(
                    (d / "_assessment.md").relative_to(base)
                ),
                "description": f"Assess {d.name}",
            })
        return {
            "action": "launch_parallel",
            "phase": 2,
            "phase_name": "Assessment",
            "agent_count": len(agents),
            "agents": agents,
        }

    # ═══════════ Phase 3: Solution Architecture — single agent ═══════════
    proposals_file = base / "research" / "_plan" / "_proposals.md"
    if not proposals_file.exists():
        logger.info("Phase 3: Launching Solution Architect")
        return {
            "action": "launch_single",
            "phase": 3,
            "phase_name": "Solution Architecture",
            "agent": "Solution Architect",
            "prompt": prompt_solution_architect(base),
            "output_file": "research/_plan/_proposals.md",
            "description": "Generate architecture proposals",
        }

    # ── Validate Phase 3 ──
    proposals_wc = word_count(proposals_file)
    logger.info("Phase 3 validate: proposals {}w", proposals_wc)
    mark_phase_done(base, 3)
    if proposals_wc < 500 and can_retry(base, "phase_3_quality"):
        logger.warning("Phase 3 RETRY: proposals only {}w < 500 — deleting", proposals_wc)
        proposals_file.unlink()
        return {
            "action": "launch_single",
            "phase": 3,
            "phase_name": "Solution Architecture (retry)",
            "agent": "Solution Architect",
            "prompt": prompt_solution_architect(base)
            + "\nRETRY: Previous output was too short. Need detailed proposals with trade-offs.",
            "output_file": "research/_plan/_proposals.md",
            "description": "Retry architecture proposals",
        }

    # ═══════════ Phase 4: Planning — build ToC ═══════════
    toc_file = base / "research" / "_plan" / "toc.md"
    if not toc_file.exists():
        logger.info("Phase 4: ToC not found, launching Planner")
        return {
            "action": "launch_single",
            "phase": 4,
            "phase_name": "Planning",
            "agent": "Planner",
            "prompt": prompt_arch_planner(base),
            "output_file": "research/_plan/toc.md",
            "description": "Build unified ToC",
        }

    # ── Validate Phase 4 ──
    toc_sections = parse_toc_sections(base)
    if not toc_sections:
        logger.warning("Phase 4 VALIDATE: ToC unparseable")
        if can_retry(base, "phase_4_parse"):
            toc_file.unlink()
            return {
                "action": "launch_single",
                "phase": 4,
                "phase_name": "Planning (retry)",
                "agent": "Planner",
                "prompt": prompt_arch_planner(base)
                + (
                    "\nRETRY: Previous ToC unparseable. "
                    "Use EXACTLY: ## NN. Title — Pages: N — Sources: path1, path2"
                ),
                "output_file": "research/_plan/toc.md",
                "description": "Retry ToC",
            }
        return {"action": "error", "message": "ToC unparseable after retry."}

    logger.info("Phase 4 OK: sections={}, total_pages={}, breakdown={}",
                len(toc_sections), sum(s['pages'] for s in toc_sections),
                [(s['num'], s['title'], f"{s['pages']}p") for s in toc_sections])

    # Save expected sections to state for tracking
    mark_phase_done(base, 4, expected_sections=[s["num"] for s in toc_sections])

    # ═══════════ Phase 5: Writing — parallel section writers ═══════════
    sections_dir = base / "draft" / "_sections"
    missing_sections = []
    for s in toc_sections:
        if not find_section_file(sections_dir, s["num"]):
            missing_sections.append(s)

    is_rev = revision_count(base) > 0

    if missing_sections:
        logger.info("Phase 5: {} sections to write{}: {}",
                    len(missing_sections),
                    " (revision)" if is_rev else "",
                    ", ".join(f"{s['num']}.{s['title']}({s['words']}w)" for s in missing_sections))

        # Sanity check: on first pass all sections must be missing
        if not is_rev and len(missing_sections) != len(toc_sections):
            logger.warning("Phase 5 MISMATCH: missing={} but toc has {} sections. "
                          "Expected all missing on first pass.",
                          len(missing_sections), len(toc_sections))

        agents = []
        for s in missing_sections:
            agents.append({
                "name": "Writer",
                "prompt": prompt_arch_writer(base, s, is_revision=is_rev),
                "output_file": f"draft/_sections/{s['filename']}",
                "description": f"Write section {s['num']}. {s['title']}",
            })

        # Track dispatched sections in state
        mark_phase_done(base, "5_dispatch",
                        sections_dispatched=[s["num"] for s in missing_sections])

        return {
            "action": "launch_parallel",
            "phase": 5,
            "phase_name": "Writing" + (" (revision)" if is_rev else ""),
            "agent_count": len(agents),
            "expected_total": len(toc_sections),
            "agents": agents,
        }

    # ── Validate Phase 5 ──
    underweight = []
    for s in toc_sections:
        f = find_section_file(sections_dir, s["num"])
        if f and word_count(f) < s["words"] * 0.5:
            underweight.append({
                "section": f"{s['num']}. {s['title']}",
                "actual": word_count(f),
                "target": s["words"],
            })

    if underweight:
        logger.warning("Phase 5 UNDERWEIGHT: {}",
                       "; ".join(f"{u['section']} actual={u['actual']}w target={u['target']}w ({u['actual']*100//max(u['target'],1)}%)" for u in underweight))
    if underweight and can_retry(base, "phase_5_wordcount"):
        agents = []
        for uw in underweight:
            s = next(x for x in toc_sections if x["num"] == uw["section"][:2])
            bad = find_section_file(sections_dir, s["num"])
            if bad:
                bad.unlink()
            agents.append({
                "name": "Writer",
                "prompt": prompt_arch_writer(base, s, is_revision=is_rev)
                + f"\nCRITICAL RETRY: Previous was {uw['actual']} words "
                f"(need {uw['target']}). Write MORE.",
                "output_file": f"draft/_sections/{s['filename']}",
                "description": f"Retry section {s['num']}",
            })
        return {
            "action": "retry",
            "phase": 5,
            "phase_name": "Writing (retry)",
            "issues": underweight,
            "agents": agents,
        }

    mark_phase_done(base, 5)

    # ═══════════ Phase 6: Editing — merge into v1.md ═══════════
    if not (base / "draft" / "v1.md").exists():
        n_files = len(list((base / 'draft' / '_sections').glob('*.md')))
        total_sec_wc = sum(word_count(f) for f in (base / 'draft' / '_sections').glob('*.md'))
        logger.info("Phase 6: Launching Editor — {} section files, total {}w", n_files, total_sec_wc)
        return {
            "action": "launch_single",
            "phase": 6,
            "phase_name": "Editing",
            "agent": "Editor",
            "prompt": prompt_arch_editor(base),
            "output_file": "draft/v1.md",
            "description": "Merge sections into v1.md",
        }

    draft_wc = word_count(base / "draft" / "v1.md")
    target_words = max_pages * 300
    logger.info("Phase 6 validate: v1.md {}w, target {}w ({}%)",
                draft_wc, target_words, draft_wc * 100 // max(target_words, 1))

    if draft_wc < target_words * 0.4 and can_retry(base, "phase_6_wordcount"):
        logger.warning("Phase 6 RETRY: {}w < 40% of target {}w — deleting v1.md", draft_wc, target_words)
        (base / "draft" / "v1.md").unlink()
        return {
            "action": "launch_single",
            "phase": 6,
            "phase_name": "Editing (retry)",
            "agent": "Editor",
            "prompt": prompt_arch_editor(base)
            + f"\nCRITICAL: Target ~{target_words} words. Do NOT lose content.",
            "output_file": "draft/v1.md",
            "description": "Retry merge",
        }

    mark_phase_done(base, 6)

    # ═══════════ Phase 7: Review — critic evaluates ═══════════
    review_file = base / "draft" / "_review.md"
    if not review_file.exists():
        logger.info("Phase 7: Launching Critic — draft {}w, target {}w", draft_wc, target_words)
        return {
            "action": "launch_single",
            "phase": 7,
            "phase_name": "Review",
            "agent": "Critic",
            "prompt": prompt_arch_critic(base, max_pages),
            "output_file": "draft/_review.md",
            "description": "Review draft",
            "info": {"draft_words": draft_wc, "target_words": target_words},
        }

    # ── Handle Verdict ──
    verdict_data = parse_verdict_details(base)
    verdict = verdict_data["verdict"]
    logger.info("Phase 7 verdict={}, issues={}, targets={}, revisions={}",
                verdict, verdict_data.get("issues", []),
                verdict_data.get("section_targets", []), revision_count(base))

    if verdict == "REVISE":
        rev_count = revision_count(base)
        if rev_count < 2:
            shutil.copy(
                review_file, base / "draft" / f"_review_v{rev_count + 1}.md"
            )
            review_file.unlink()
            (base / "draft" / "v1.md").unlink(missing_ok=True)

            # Targeted revision: only delete sections that need rework
            targeted = verdict_data.get("section_targets", [])
            if targeted:
                for f in (base / "draft" / "_sections").glob("*.md"):
                    sec_num = f.stem[:2]
                    if sec_num in targeted:
                        logger.info("Phase 7 REVISE: deleting targeted section {}", f.name)
                        f.unlink()
            else:
                # No specific targets — delete all sections (legacy behavior)
                for f in (base / "draft" / "_sections").glob("*.md"):
                    f.unlink()

            mark_phase_done(base, "7_revise",
                            revision_count=rev_count + 1,
                            revision_targets=targeted,
                            revision_issues=verdict_data.get("issues", []))
            return cmd_next(base_folder)

    # ═══════════ Phase 8: Illustration — ORCHESTRATOR runs PaperBanana ═══════════
    draft_path = base / "draft" / "v1.md"
    if not draft_path.exists():
        return {
            "action": "error",
            "message": "No draft found at draft/v1.md",
        }

    draft_text = draft_path.read_text(encoding="utf-8")
    has_png_refs = bool(re.search(r"!\[.*?\]\(.*?\.png\)", draft_text))
    manifest = base / "illustrations" / "_manifest.md"
    fig_label = "Рис." if "russian" in params.get("language", "english").lower() else "Fig."
    ill_mode = params.get("illustration mode", "pipeline").strip().lower()

    if not manifest.exists() and "8_dispatch" not in state.get("completed_phases", []):
        logger.info("Phase 8: Illustration — manifest missing, generating (mode={})", ill_mode)
        if not os.environ.get("OPENAI_API_KEY"):
            logger.warning("Phase 8: OPENAI_API_KEY not set, skipping illustrations")
            return {
                "action": "warning",
                "phase": 8,
                "phase_name": "Illustration (skipped)",
                "message": "OPENAI_API_KEY not set. Skipping illustrations.",
            }

        placeholders = re.findall(r"<!-- ILLUSTRATION:(.+?)-->", draft_text)
        logger.debug("Phase 8: found {} ILLUSTRATION placeholders in draft", len(placeholders))
        illustrations = []
        for i, ph in enumerate(placeholders, 1):
            desc_m = re.search(r'description="([^"]+)"', ph)
            type_m = re.search(r'type="([^"]+)"', ph)
            desc = desc_m.group(1) if desc_m else f"Architecture diagram {i}"
            itype = type_m.group(1) if type_m else "architecture"
            short_desc = desc[:80]
            illustrations.append({
                "index": i,
                "type": itype,
                "description": desc,
                "placeholder": f"<!-- ILLUSTRATION:{ph}-->",
                "output_png": f"illustrations/diagram_{i}.png",
                "embed_as": (
                    f"![{fig_label} {i}. {short_desc}](../illustrations/diagram_{i}.png)\n\n"
                    f"*{fig_label} {i}. {short_desc}*"
                ),
            })

        if not illustrations:
            fallback_items = [
                (1, "architecture", "Current vs proposed architecture overview"),
                (2, "comparison", "Architecture options comparison matrix"),
            ]
            illustrations = [
                {
                    "index": idx,
                    "type": itype,
                    "description": desc,
                    "output_png": f"illustrations/diagram_{idx}.png",
                    "embed_as": (
                        f"![{fig_label} {idx}. {desc}](../illustrations/diagram_{idx}.png)\n\n"
                        f"*{fig_label} {idx}. {desc}*"
                    ),
                }
                for idx, itype, desc in fallback_items
            ]

        mark_phase_done(base, "8_dispatch")
        direct_flag = " --direct" if ill_mode == "direct" else ""
        return {
            "action": "orchestrator_illustrate_parallel",
            "phase": 8,
            "phase_name": "Illustration (parallel)",
            "count": len(illustrations),
            "illustrations": illustrations,
            "fig_label": fig_label,
            "draft_file": "draft/v1.md",
            "command_template": (
                "python3 .github/skills/image-generator/scripts/"
                f"paperbanana_generate.py \"{{description}}\" "
                f"\"{{output_path}}\"{direct_flag}"
                + (" --context \"{{context}}\" --critic-rounds 2" if ill_mode != "direct" else "")
            ),
            "instructions": (
                "PARALLEL GENERATION — launch ALL illustrations simultaneously:\n\n"
                "1. Start ALL illustration commands as BACKGROUND processes via "
                "run_in_terminal(isBackground=true) — one per illustration.\n"
                "   Each command: replace {description}, {output_path}, {context} in command_template.\n"
                "   {context} = 200-500 words of relevant section text from the draft.\n\n"
                "2. Poll ALL background terminals via get_terminal_output until ALL complete.\n\n"
                "3. After ALL finish: embed each in draft/v1.md — replace placeholder with embed_as.\n\n"
                "4. MANDATORY: Write illustrations/_manifest.md with:\n"
                "   a) Summary table (file, section, type, description)\n"
                "   b) Generation details (model, critic rounds, date)\n"
                "   c) Regeneration Prompts section — for EACH diagram record:\n"
                "      - The exact description string\n"
                "      - The exact context string\n"
                "      - Full copy-paste CLI command for one-command regeneration\n\n"
                "5. VERIFY: grep '.png' in draft/v1.md — must find refs for all illustrations."
            ),
        }

    pngs = list((base / "illustrations").glob("*.png"))

    # Guard: 8_dispatch set but illustrations not yet finished
    if not manifest.exists() and "8_dispatch" in state.get("completed_phases", []):
        if not pngs:
            return {
                "action": "wait",
                "phase": 8,
                "phase_name": "Illustration (awaiting generation)",
                "message": (
                    "Illustrations dispatched but not yet generated. "
                    "Wait for PaperBanana background processes to finish, "
                    "then copy PNGs to illustrations/, embed in v1.md, "
                    "and write illustrations/_manifest.md."
                ),
            }
        # PNGs exist but manifest not written — need embed + manifest
        if not has_png_refs:
            return {
                "action": "orchestrator_illustrate",
                "phase": 8,
                "phase_name": "Illustration (embed + manifest)",
                "count": len(pngs),
                "illustrations": [
                    {
                        "index": i + 1,
                        "output_png": f"illustrations/{p.name}",
                        "embed_as": (
                            f"![{fig_label} {i + 1}. {p.stem}](../illustrations/{p.name})\n\n"
                            f"*{fig_label} {i + 1}. {p.stem}*"
                        ),
                    }
                    for i, p in enumerate(sorted(pngs))
                ],
                "fig_label": fig_label,
                "draft_file": "draft/v1.md",
                "instructions": (
                    "PNGs generated. Embed each in draft/v1.md (replace ILLUSTRATION placeholders), "
                    "then write illustrations/_manifest.md with summary table + regeneration prompts "
                    "(description, context, full CLI command per diagram)."
                ),
            }

    if pngs and not has_png_refs and can_retry(base, "phase_8_embed"):
        manifest.unlink()
        return {
            "action": "orchestrator_illustrate",
            "phase": 8,
            "phase_name": "Illustration (retry — embed)",
            "count": len(pngs),
            "illustrations": [
                {
                    "index": i + 1,
                    "output_png": f"illustrations/{p.name}",
                    "embed_as": (
                        f"![{fig_label} {i + 1}. {p.stem}](../illustrations/{p.name})\n\n"
                        f"*{fig_label} {i + 1}. {p.stem}*"
                    ),
                }
                for i, p in enumerate(pngs)
            ],
            "fig_label": fig_label,
            "draft_file": "draft/v1.md",
            "instructions": "PNGs exist but not in draft/v1.md. Embed them (image + caption). Rewrite manifest with regeneration prompts.",
        }

    mark_phase_done(base, 8)

    # ═══════════ Phase 9: Delivery ═══════════
    final_wc = word_count(draft_path)
    logger.success("Phase 9: COMPLETE — {}w, ~{:.1f} pages, {} sections, {} assessments, {} illustrations",
                   final_wc, final_wc / 300, len(toc_sections),
                   sum(1 for _ in base.glob('research/*/_assessment.md')),
                   len(list((base / 'illustrations').glob('*.png'))))
    return {
        "action": "complete",
        "phase": 9,
        "phase_name": "Delivery",
        "document": str(draft_path),
        "stats": {
            "words": final_wc,
            "pages_approx": round(final_wc / 300, 1),
            "sections": len(toc_sections),
            "extracts": sum(
                1 for _ in base.glob("research/*/extract_*.md")
            ),
            "assessments": sum(
                1 for _ in base.glob("research/*/_assessment.md")
            ),
            "has_proposals": (
                base / "research" / "_plan" / "_proposals.md"
            ).exists(),
            "illustrations_png": len(
                list((base / "illustrations").glob("*.png"))
            ),
            "illustrations_embedded": bool(
                re.search(
                    r"!\[.*?\]\(.*?\.png\)",
                    draft_path.read_text(encoding="utf-8"),
                )
            ),
            "verdict": parse_verdict(base),
            "revisions": revision_count(base),
        },
        "next_steps": [
            "PDF export: @pdf-exporter",
            "Confluence publish: @confluence-publisher",
        ],
    }


def cmd_status(base_folder: str) -> dict:
    base = Path(base_folder).resolve()
    if not base.exists():
        return {"error": f"Folder {base} does not exist"}

    params = parse_arch_params(base)
    source_dirs = get_source_dirs(base)
    sections_dir = base / "draft" / "_sections"
    v1 = base / "draft" / "v1.md"

    status = {
        "folder": str(base),
        "pipeline": "architecture",
        "params": {
            "topic": params.get("topic", "?"),
            "max_pages": params.get("max_pages", "?"),
            "sources": len(params.get("sources", [])),
            "source_types": list(
                {s["type"] for s in params.get("sources", [])}
            ),
        },
        "phases": {},
    }

    # Phase 1: Source extraction
    extract_info = {}
    for d in source_dirs:
        exts = list(d.glob("extract_*.md"))
        extract_info[d.name] = {
            "count": len(exts),
            "total_words": sum(word_count(e) for e in exts),
        }
    status["phases"]["1_extraction"] = extract_info

    # Phase 2: Assessments
    status["phases"]["2_assessment"] = {
        d.name: (d / "_assessment.md").exists() for d in source_dirs
    }

    # Phase 3: Proposals
    proposals = base / "research" / "_plan" / "_proposals.md"
    status["phases"]["3_proposals"] = {
        "has_proposals": proposals.exists(),
        "words": word_count(proposals),
    }

    # Phase 4: ToC
    toc = parse_toc_sections(base)
    status["phases"]["4_planning"] = {
        "has_toc": (base / "research" / "_plan" / "toc.md").exists(),
        "sections": len(toc),
        "total_pages": sum(s["pages"] for s in toc) if toc else 0,
    }

    # Phase 5: Writing
    section_info = {}
    for s in toc:
        f = find_section_file(sections_dir, s["num"])
        if f:
            wc = word_count(f)
            section_info[s["num"]] = {
                "file": f.name,
                "words": wc,
                "target": s["words"],
                "pct": round(wc / max(s["words"], 1) * 100),
            }
        else:
            section_info[s["num"]] = {
                "file": None,
                "words": 0,
                "target": s["words"],
            }
    status["phases"]["5_writing"] = {"sections": section_info}

    # Phase 6: Editing
    status["phases"]["6_editing"] = {
        "has_draft": v1.exists(),
        "words": word_count(v1),
    }

    # Phase 7: Review
    status["phases"]["7_review"] = {
        "has_review": (base / "draft" / "_review.md").exists(),
        "verdict": parse_verdict(base),
        "revisions": revision_count(base),
    }

    # Phase 8: Illustrations
    pngs = list((base / "illustrations").glob("*.png"))
    dt = v1.read_text(encoding="utf-8") if v1.exists() else ""
    status["phases"]["8_illustration"] = {
        "png_files": len(pngs),
        "embedded_refs": len(re.findall(r"!\[.*?\]\(.*?\.png\)", dt)),
        "manifest": (base / "illustrations" / "_manifest.md").exists(),
    }

    status["retries"] = load_retries(base)
    return status


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print(
            json.dumps(
                {
                    "error": "Usage: arch_pipeline_runner.py <command> [base_folder]",
                    "commands": {
                        "init [folder]": "Create folder structure",
                        "next <folder>": "Get next pipeline action",
                        "status <folder>": "Full status report",
                    },
                },
                indent=2,
            )
        )
        sys.exit(1)

    command = sys.argv[1]

    if command == "init":
        folder = (
            sys.argv[2]
            if len(sys.argv) >= 3
            else f"generated_arch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        result = cmd_init(folder)
    elif command in ("next", "status"):
        if len(sys.argv) < 3:
            print(
                json.dumps(
                    {
                        "error": f"Usage: arch_pipeline_runner.py {command} <base_folder>"
                    }
                )
            )
            sys.exit(1)
        result = (
            cmd_next(sys.argv[2]) if command == "next" else cmd_status(sys.argv[2])
        )
    else:
        result = {"error": f"Unknown command: {command}"}

    logger.debug("CMD {}: action={}, phase={}", command,
                 result.get("action", result.get("status", "?")),
                 result.get("phase", "-"))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    # Prevent BrokenPipeError when stdout is closed early (e.g. run_in_terminal timeout)
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    try:
        main()
    except Exception as e:
        logger.opt(exception=True).error("Script crash: {}", e)
        print(json.dumps({"action": "error", "message": f"Script error: {e}"}, ensure_ascii=False))
        sys.exit(1)
