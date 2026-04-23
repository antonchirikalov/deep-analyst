#!/usr/bin/env python3
"""
Deterministic Pipeline Runner v2 for deep-analyst research pipeline.

Architecture: Sub-agents RETURN text — orchestrator writes it to disk.
Exception: Researcher writes files directly (writes_own_files: True).

Usage:
    python3 .github/scripts/research_pipeline_runner.py init [base_folder]
    python3 .github/scripts/research_pipeline_runner.py next <base_folder>
    python3 .github/scripts/research_pipeline_runner.py status <base_folder>
"""

import json
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
_PROJECT_ROOT = _SCRIPT_DIR.parent.parent  # .github/scripts → project root
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

# ═══════════════════════════════════════════════════════════════
# LOGGING  (loguru: stderr=INFO, file=DEBUG with rotation)
# ═══════════════════════════════════════════════════════════════

# Remove default sink, add stderr with INFO
logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    format="<level>[{level.name[0]}]</level> <cyan>{function}</cyan>: {message}",
    colorize=True,
)

_file_sinks: dict[str, int] = {}  # path → sink_id, prevents duplicates


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
# TRANSLITERATION & SLUGIFY
# ═══════════════════════════════════════════════════════════════

_TRANSLIT = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
}


def slugify(text: str) -> str:
    text = text.lower().strip()
    result = []
    for ch in text:
        if ch in _TRANSLIT:
            result.append(_TRANSLIT[ch])
        elif ch.isascii():
            result.append(ch)
    text = ''.join(result)
    text = re.sub(r'[^a-z0-9]+', '_', text)
    return text.strip('_')[:60]


# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def count_urls(path: Path) -> int:
    if not path.exists():
        return 0
    return len(re.findall(r'https?://', path.read_text(encoding='utf-8')))


def word_count(path: Path) -> int:
    if not path.exists():
        return 0
    return len(path.read_text(encoding='utf-8').split())


def get_subtopic_dirs(base: Path) -> list:
    research = base / "research"
    if not research.exists():
        return []
    return sorted([
        d for d in research.iterdir()
        if d.is_dir() and d.name != "_plan"
    ])


def parse_params(base: Path) -> dict:
    params_file = base / "research" / "_plan" / "params.md"
    if not params_file.exists():
        return {}
    text = params_file.read_text(encoding='utf-8')
    params = {}

    for line in text.splitlines():
        m = re.match(r'-\s+\*\*(.+?):?\*\*:?\s*(.+)', line)
        if m:
            key = m.group(1).strip().lower()
            val = m.group(2).strip()
            params[key] = val

    for key in ['max pages', 'max_pages']:
        if key in params and isinstance(params[key], str):
            m2 = re.search(r'(\d+)', params[key])
            if m2:
                params['max_pages'] = int(m2.group(1))
                break

    subtopics = []
    in_sub = False
    for line in text.splitlines():
        if re.search(r'##\s*(Subtopics|Подтемы)', line, re.IGNORECASE):
            in_sub = True
            continue
        if in_sub:
            m3 = re.match(r'\s*\d+\.\s+(.+)', line)
            if m3:
                subtopics.append(m3.group(1).strip())
            elif line.strip().startswith('#'):
                break
    params['subtopics'] = subtopics
    params['topic'] = params.get('topic', params.get('тема', 'Research'))
    return params


def parse_toc_sections(base: Path) -> list:
    toc_file = base / "research" / "_plan" / "toc.md"
    if not toc_file.exists():
        return []
    text = toc_file.read_text(encoding='utf-8')
    sections = []
    current = None

    for line in text.splitlines():
        m = re.match(r'##\s+0*(\d+)\.\s+(.+)', line)
        if m:
            if current:
                sections.append(current)
            num = m.group(1).zfill(2)
            rest = m.group(2)
            title = re.split(r'\s*[—–-]\s*(?:Pages?|Стр|Sources?|Источник)', rest, flags=re.IGNORECASE)[0].strip()
            pm = re.search(r'(?:Pages?|Стр)[:\s]*(\d+)', rest, re.IGNORECASE)
            pages = int(pm.group(1)) if pm else 2
            sm = re.search(r'(?:Sources?|Источник\w*)[:\s]*(.+?)(?:\s*[—–-]|$)', rest, re.IGNORECASE)
            sources = sm.group(1).strip() if sm else ""
            slug = slugify(title)
            current = {
                "num": num, "title": title, "pages": pages,
                "words": pages * 300, "sources": sources,
                "filename": f"{num}_{slug}.md", "slug": slug,
            }
        elif current:
            pm = re.match(r'\s*(?:Pages?|Стр)[:\s]*(\d+)', line, re.IGNORECASE)
            if pm:
                current["pages"] = int(pm.group(1))
                current["words"] = current["pages"] * 300
            sm = re.match(r'\s*(?:Sources?|Источник\w*)[:\s]*(.+)', line, re.IGNORECASE)
            if sm:
                current["sources"] = sm.group(1).strip()

    if current:
        sections.append(current)
    return sections


def parse_verdict(base: Path) -> str:
    review = base / "draft" / "_review.md"
    if not review.exists():
        return "NONE"
    text = review.read_text(encoding='utf-8')
    # Try structured JSON verdict first (new format)
    json_m = re.search(r'```json\s*\n\s*(\{.*?"verdict".*?\})\s*\n\s*```', text, re.DOTALL)
    if json_m:
        try:
            verdict_data = json.loads(json_m.group(1))
            v = verdict_data.get("verdict", "").upper()
            if v in ("APPROVED", "REVISE"):
                return v
        except (json.JSONDecodeError, AttributeError):
            pass
    # Fallback: regex on markdown headers (legacy format)
    if re.search(r'Verdict.*APPROVED', text, re.IGNORECASE):
        return "APPROVED"
    if re.search(r'Verdict.*REVISE', text, re.IGNORECASE):
        return "REVISE"
    return "UNKNOWN"


def parse_verdict_details(base: Path) -> dict:
    """Parse the structured verdict JSON block from review. Returns dict with verdict, issues, section_targets."""
    review = base / "draft" / "_review.md"
    if not review.exists():
        return {"verdict": "NONE", "issues": [], "section_targets": []}
    text = review.read_text(encoding='utf-8')
    json_m = re.search(r'```json\s*\n\s*(\{.*?"verdict".*?\})\s*\n\s*```', text, re.DOTALL)
    if json_m:
        try:
            data = json.loads(json_m.group(1))
            return {
                "verdict": data.get("verdict", "UNKNOWN").upper(),
                "issues": data.get("issues", []),
                "section_targets": data.get("section_targets", []),
            }
        except (json.JSONDecodeError, AttributeError):
            pass
    # Fallback
    verdict = "UNKNOWN"
    if re.search(r'Verdict.*APPROVED', text, re.IGNORECASE):
        verdict = "APPROVED"
    elif re.search(r'Verdict.*REVISE', text, re.IGNORECASE):
        verdict = "REVISE"
    return {"verdict": verdict, "issues": [], "section_targets": []}


def find_section_file(sections_dir: Path, num: str):
    if not sections_dir.exists():
        return None
    for f in sections_dir.glob("*.md"):
        if f.stem.startswith(num) or f.stem.startswith(str(int(num))):
            return f
    return None


def load_retries(base: Path) -> dict:
    f = base / ".retries.json"
    if f.exists():
        return json.loads(f.read_text())
    return {}


def save_retries(base: Path, retries: dict):
    (base / ".retries.json").write_text(json.dumps(retries))


def can_retry(base: Path, key: str, max_retries: int = 1) -> bool:
    retries = load_retries(base)
    count = retries.get(key, 0)
    if count >= max_retries:
        return False
    retries[key] = count + 1
    save_retries(base, retries)
    return True


def revision_count(base: Path) -> int:
    return len(list(base.glob("draft/_review_v*.md")))


# ═══════════════════════════════════════════════════════════════
# PROMPT BUILDERS — sub-agents READ files, RETURN text
# Orchestrator writes the returned text to output_file
# (Researcher is special: it writes files DIRECTLY)
# ═══════════════════════════════════════════════════════════════

def prompt_researcher(base: Path, subtopic_slug: str, main_topic: str,
                      extract_only: bool = False) -> str:
    name = subtopic_slug.replace('_', ' ')
    folder = f'{base}/research/{subtopic_slug}'
    links_file = f'{folder}/_links.md'

    if extract_only:
        return (
            f'You are a Researcher. Extract content from sources for subtopic "{name}".\n'
            f'Overall topic: "{main_topic}"\n\n'
            f'STEP 1: Load tools — call tool_search_tool_regex with pattern '
            f'"tavily|fetch_webpage|mcp_github|mcp_huggingface|mcp_mcp-atlassian"\n\n'
            f'STEP 2: Read sources from {links_file}\n\n'
            f'STEP 3: For EACH source, extract full content:\n'
            f'  - Web URLs: try tavily_extract → fallback fetch_webpage\n'
            f'  - GitHub files: use mcp_github_get_file_contents(owner, repo, path)\n'
            f'  - Confluence: use mcp_mcp-atlassian_confluence_get_page(page_id)\n'
            f'  - Write to {folder}/extract_N.md with header:\n'
            f'     # Extract: [title]\\nSource: [url]\\nWords: ~N\\n\\n[FULL content]\n'
            f'  - Do NOT summarize — copy VERBATIM. Include all code blocks, JSON, CLI.\n'
            f'  - Skip failed sources, continue to next.\n\n'
            f'RETURN a brief summary: how many sources processed, total words extracted.'
        )

    return (
        f'You are a Researcher. Perform deep search and extraction for subtopic "{name}".\n'
        f'Overall topic: "{main_topic}"\n\n'
        f'STEP 1: Load tools — call tool_search_tool_regex with pattern '
        f'"tavily|fetch_webpage|mcp_github|mcp_huggingface|mcp_mcp-atlassian"\n\n'
        f'STEP 2: Search for sources using MULTIPLE channels:\n'
        f'  a. Web: mcp_tavily-remote_tavily_search('
        f'query="{name} technical deep dive documentation", max_results=10)\n'
        f'     If fails: try "{name} guide tutorial overview"\n'
        f'  b. GitHub (for OSS/code topics): mcp_github_search_repositories(query="{name}")\n'
        f'     Then read key files: README.md, docs/, architecture files\n'
        f'  c. HuggingFace (for ML/AI topics): mcp_huggingface_paper_search(query="{name}")\n'
        f'     Also try: mcp_huggingface_hf_doc_search(query="{name}")\n'
        f'  d. Confluence (for internal topics): mcp_mcp-atlassian_confluence_search(query="{name}")\n'
        f'     Then read pages: mcp_mcp-atlassian_confluence_get_page(page_id)\n'
        f'  e. If all fail: use your knowledge to list known documentation URLs\n'
        f'  f. Write numbered list to {links_file}:\n'
        f'     1. URL — Title\\n     2. URL — Title\\n     ...\n\n'
        f'STEP 3: Extract content from EACH source\n'
        f'  - Web URLs: try tavily_extract → fallback fetch_webpage\n'
        f'  - GitHub files: use mcp_github_get_file_contents(owner, repo, path)\n'
        f'  - Confluence pages: use mcp_mcp-atlassian_confluence_get_page(page_id)\n'
        f'  - Write to {folder}/extract_N.md with header:\n'
        f'     # Extract: [title]\\nSource: [url]\\nWords: ~N\\n\\n[FULL content]\n'
        f'  - Do NOT summarize — copy VERBATIM. Include ALL code blocks, JSON, CLI.\n'
        f'  - Skip failed sources, continue to next.\n\n'
        f'TARGET: 5+ sources extracted, 800+ words average per extract.\n'
        f'Use GitHub for source code topics, HuggingFace for ML topics, Tavily for everything else.\n\n'
        f'RETURN a brief summary: sources found, extracts written, total words.'
    )

def prompt_analyst(base: Path, subtopic_slug: str, main_topic: str) -> str:
    return (
        f'You are a research Analyst. Analyze extracted content for subtopic '
        f'"{subtopic_slug.replace("_", " ")}".\n'
        f'Overall research topic: "{main_topic}"\n\n'
        f'Read ALL extract_*.md files in: {base}/research/{subtopic_slug}/\n\n'
        f'YOUR TASK:\n'
        f'1. Analyze depth of each extract\n'
        f'2. Propose document sections from these extracts\n'
        f'3. Mark each: DEEP (enough for 2000+ words) or SHALLOW\n'
        f'4. Map which extract files support which sections\n'
        f'5. Note gaps in coverage\n\n'
        f'RETURN your analysis as markdown. Start directly with content.'
    )


def prompt_planner(base: Path) -> str:
    return (
        f'You are a research Planner. Build a unified Table of Contents.\n\n'
        f'Read these files:\n'
        f'- {base}/research/_plan/params.md (topic, max_pages, audience, language)\n'
        f'- All {base}/research/*/_structure.md files\n\n'
        f'FORMAT (MANDATORY — pipeline parses with regex):\n'
        f'## NN. Section Title — Pages: N — Sources: subtopic_folder1, subtopic_folder2\n\n'
        f'Example:\n'
        f'## 01. Introduction — Pages: 2 — Sources: all\n'
        f'## 02. GitHub Copilot Architecture — Pages: 4 — Sources: github_copilot_coding_agent_architecture\n\n'
        f'Total pages MUST match max_pages from params.md (+-1).\n'
        f'1 page = 300 words.\n\n'
        f'RETURN the ToC as markdown. Start directly with content.'
    )


def prompt_writer(base: Path, section: dict, is_revision: bool = False) -> str:
    words = section["words"]
    revision_note = ""
    if is_revision:
        reviews = sorted(base.glob("draft/_review_v*.md"))
        if reviews:
            revision_note = (
                f'\n\nREVISION MODE: Read {reviews[-1]} for Critic feedback. '
                f'Address ALL feedback. Revision #{len(reviews)}.'
            )

    return (
        f'You are a technical Writer. Write one section of a research document.\n\n'
        f'Section: {section["num"]}. {section["title"]}\n'
        f'Page budget: {section["pages"]} pages ({words} words MINIMUM)\n\n'
        f'Read these files:\n'
        f'- {base}/research/_plan/params.md (language, audience, tone)\n'
        f'- Source extracts in: {section["sources"]} '
        f'(read extract_*.md files in those subtopic folders under {base}/research/)\n'
        f'{revision_note}\n\n'
        f'MANDATORY RULES:\n'
        f'1. WORD COUNT: Section MUST be at least {words} words.\n'
        f'2. TECHNICAL DEPTH: Include ALL technical details from extracts — '
        f'code blocks, JSON, file paths, CLI commands. Copy VERBATIM.\n'
        f'3. ILLUSTRATION PLACEHOLDERS: At least 1 per 2+ page section:\n'
        f'   <!-- ILLUSTRATION: type="architecture|comparison|pipeline", '
        f'section="{section["num"]}. {section["title"]}", '
        f'description="Detailed description of visualization" -->\n'
        f'   Follow EVERY placeholder with a caption: *Рис. N. Short caption*\n'
        f'4. NO FILLER: Ban "мощный", "инновационный", "comprehensive", "революционный".\n'
        f'5. LANGUAGE: Write in the language from params.md.\n\n'
        f'RETURN the section as markdown starting with ## heading. No preamble.'
    )


def prompt_editor(base: Path) -> str:
    return (
        f'You are a document Editor. Merge all sections into one cohesive document.\n\n'
        f'Read these files:\n'
        f'- {base}/research/_plan/toc.md (section order)\n'
        f'- {base}/research/_plan/params.md (language, title)\n'
        f'- All files in {base}/draft/_sections/ (in NN_ order)\n\n'
        f'RULES:\n'
        f'- Maintain ToC order (01, 02, 03...)\n'
        f'- Add # title and executive summary at top\n'
        f'- Add transitions between sections\n'
        f'- Remove duplicated content (keep fullest version)\n'
        f'- Preserve ALL <!-- ILLUSTRATION: ... --> placeholders\n'
        f'- Do NOT reduce word count\n\n'
        f'RETURN the merged document as markdown. Start with # title.'
    )


def prompt_critic(base: Path, max_pages: int) -> str:
    min_words = int(max_pages * 300 * 0.8)
    return (
        f'You are a document Critic. Review the draft for quality.\n\n'
        f'Read these files:\n'
        f'- {base}/draft/v1.md (draft)\n'
        f'- {base}/research/_plan/params.md (parameters)\n'
        f'- {base}/research/_plan/toc.md (page budgets)\n\n'
        f'CRITICAL RULES:\n'
        f'1. If document <{min_words} words for {max_pages}-page target -> REVISE.\n'
        f'2. If ANY section mentions concepts without explaining HOW -> REVISE.\n'
        f'3. Check filler language ("мощный", "comprehensive" without substance).\n'
        f'4. Check section word counts vs ToC budgets (+-15%).\n'
        f'5. Check for duplicated content.\n'
        f'6. Verdict: ## Verdict: APPROVED or ## Verdict: REVISE\n'
        f'7. If REVISE: list specific sections and issues.\n\n'
        f'RETURN your review as markdown. No preamble.'
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
    logger.info("INIT folder={}", base)
    return {
        "status": "ready",
        "folder": str(base),
        "next_step": "Write research/_plan/params.md, then run next",
    }


def cmd_next(base_folder: str) -> dict:
    base = Path(base_folder).resolve()
    if not base.exists():
        return {"action": "error", "message": f"Folder {base} does not exist."}

    _setup_file_log(base)
    params = parse_params(base)
    retries = load_retries(base)
    if retries:
        logger.debug("Retry state: {}", retries)

    # ── Phase 0 ──
    if not params or not params.get('subtopics'):
        logger.info("Phase 0: params not found or no subtopics")
        return {
            "action": "agent_task", "phase": 0,
            "phase_name": "Decomposition",
            "message": "Write research/_plan/params.md with Topic, Max pages, Subtopics.",
        }

    main_topic = params.get('topic', 'Research')
    max_pages = params.get('max_pages', 25)
    subtopics = params['subtopics']
    logger.info("Params: topic={!r}, max_pages={}, subtopics={}",
                main_topic, max_pages, len(subtopics))

    for st in subtopics:
        slug = slugify(st)
        (base / "research" / slug).mkdir(parents=True, exist_ok=True)

    subtopic_dirs = get_subtopic_dirs(base)

    # ═══════════ Phase 1: Research — Researcher sub-agents (parallel) ═══════════
    # Each Researcher searches + extracts for one subtopic, writes files directly
    needs_research = [d for d in subtopic_dirs if not list(d.glob("extract_*.md"))]
    if needs_research:
        logger.info("Phase 1: {} subtopics need research: {}",
                    len(needs_research), [d.name for d in needs_research])
        agents = []
        for d in needs_research:
            has_links = (d / "_links.md").exists()
            name = d.name.replace('_', ' ')
            agents.append({
                "name": "Researcher",
                "prompt": prompt_researcher(base, d.name, main_topic, extract_only=has_links),
                "writes_own_files": True,
                "verify_dir": str(d.relative_to(base)),
                "description": f"Research {name}",
            })
        return {
            "action": "launch_parallel",
            "phase": 1, "phase_name": "Research",
            "agent_count": len(agents), "agents": agents,
        }

    # ── Validate Phase 1: research quality ──
    extract_issues = []
    for d in subtopic_dirs:
        exts = list(d.glob("extract_*.md"))
        urls = count_urls(d / "_links.md")
        n_ext = len(exts)
        avg_wc = sum(word_count(e) for e in exts) / max(n_ext, 1)
        logger.debug("Phase 1 validate: {} — extracts={}, urls={}, avg_wc={}",
                     d.name, n_ext, urls, int(avg_wc))
        if n_ext < max(int(urls * 0.4), 2) and n_ext < 3:
            extract_issues.append({
                "subtopic": d.name, "extracts": n_ext, "urls": urls,
                "avg_words": int(avg_wc), "issue": f"Only {n_ext} from {urls} URLs",
            })
        elif avg_wc < 400:
            extract_issues.append({
                "subtopic": d.name, "extracts": n_ext, "urls": urls,
                "avg_words": int(avg_wc), "issue": "Too shallow",
            })

    if extract_issues and can_retry(base, "phase_1_quality"):
        logger.warning("Phase 1 RETRY: {} issues: {}",
                       len(extract_issues),
                       [(i['subtopic'], i['issue'], f"exts={i['extracts']}", f"avg={i['avg_words']}w") for i in extract_issues])
        agents = []
        for issue in extract_issues:
            d = base / "research" / issue["subtopic"]
            agents.append({
                "name": "Researcher",
                "prompt": prompt_researcher(base, issue["subtopic"], main_topic,
                                            extract_only=True) +
                    f'\nRETRY: Previous had {issue["extracts"]} extracts, '
                    f'avg {issue["avg_words"]} words. Extract MORE URLs with MORE depth.',
                "writes_own_files": True,
                "verify_dir": str(d.relative_to(base)),
                "description": f"Retry research {issue['subtopic']}",
            })
        return {
            "action": "retry",
            "phase": 1, "phase_name": "Research (retry)",
            "issues": extract_issues, "agents": agents,
        }

    # ═══════════ Phase 2: Analysis — sub-agent returns text ═══════════
    missing_structures = [d for d in subtopic_dirs if not (d / "_structure.md").exists()]
    if missing_structures:
        logger.info("Phase 2: {} subtopics need analysis: {}",
                    len(missing_structures), [d.name for d in missing_structures])
        agents = []
        for d in missing_structures:
            agents.append({
                "name": "Analyst",
                "prompt": prompt_analyst(base, d.name, main_topic),
                "output_file": str((d / "_structure.md").relative_to(base)),
                "description": f"Analyze {d.name}",
            })
        return {
            "action": "launch_parallel",
            "phase": 2, "phase_name": "Analysis",
            "agent_count": len(agents), "agents": agents,
        }

    # ═══════════ Phase 3: Planning — sub-agent returns text ═══════════
    if not (base / "research" / "_plan" / "toc.md").exists():
        logger.info("Phase 3: ToC not found, launching Planner")
        return {
            "action": "launch_single",
            "phase": 3, "phase_name": "Planning",
            "agent": "Planner",
            "prompt": prompt_planner(base),
            "output_file": "research/_plan/toc.md",
            "description": "Build unified ToC",
        }

    # ── Validate Phase 3 ──
    toc_sections = parse_toc_sections(base)
    if not toc_sections:
        logger.warning("Phase 3 VALIDATE: ToC unparseable")
        if can_retry(base, "phase_3_parse"):
            (base / "research" / "_plan" / "toc.md").unlink()
            return {
                "action": "launch_single",
                "phase": 3, "phase_name": "Planning (retry)",
                "agent": "Planner",
                "prompt": prompt_planner(base) + (
                    "\nRETRY: Previous ToC unparseable. "
                    "Use EXACTLY: ## NN. Title — Pages: N — Sources: path1, path2"
                ),
                "output_file": "research/_plan/toc.md",
                "description": "Retry ToC",
            }
        return {"action": "error", "message": "ToC unparseable."}

    logger.info("Phase 3 OK: sections={}, total_pages={}, breakdown={}",
                len(toc_sections), sum(s['pages'] for s in toc_sections),
                [(s['num'], s['title'], f"{s['pages']}p") for s in toc_sections])

    # ═══════════ Phase 4: Writing — sub-agents return text ═══════════
    sections_dir = base / "draft" / "_sections"
    missing_sections = []
    for s in toc_sections:
        if not find_section_file(sections_dir, s["num"]):
            missing_sections.append(s)

    is_rev = revision_count(base) > 0

    if missing_sections:
        logger.info("Phase 4: {} sections to write{}: {}",
                    len(missing_sections),
                    " (revision)" if is_rev else "",
                    ", ".join(f"{s['num']}.{s['title']}({s['words']}w)" for s in missing_sections))
        agents = []
        for s in missing_sections:
            agents.append({
                "name": "Writer",
                "prompt": prompt_writer(base, s, is_revision=is_rev),
                "output_file": f"draft/_sections/{s['filename']}",
                "description": f"Write section {s['num']}. {s['title']}",
            })
        return {
            "action": "launch_parallel",
            "phase": 4, "phase_name": "Writing" + (" (revision)" if is_rev else ""),
            "agent_count": len(agents), "agents": agents,
        }

    # ── Validate Phase 4 ──
    underweight = []
    for s in toc_sections:
        f = find_section_file(sections_dir, s["num"])
        if f and word_count(f) < s["words"] * 0.5:
            underweight.append({
                "section": f"{s['num']}. {s['title']}",
                "actual": word_count(f), "target": s["words"],
            })

    if underweight:
        logger.warning("Phase 4 UNDERWEIGHT: {}",
                       "; ".join(f"{u['section']} actual={u['actual']}w target={u['target']}w ({u['actual']*100//max(u['target'],1)}%)" for u in underweight))
    if underweight and can_retry(base, "phase_4_wordcount"):
        agents = []
        for uw in underweight:
            s = next(x for x in toc_sections if x["num"] == uw["section"][:2])
            bad = find_section_file(sections_dir, s["num"])
            if bad:
                bad.unlink()
            agents.append({
                "name": "Writer",
                "prompt": prompt_writer(base, s, is_revision=is_rev) +
                    f"\nCRITICAL RETRY: Previous was {uw['actual']} words (need {uw['target']}). Write MORE.",
                "output_file": f"draft/_sections/{s['filename']}",
                "description": f"Retry section {s['num']}",
            })
        return {
            "action": "retry",
            "phase": 4, "phase_name": "Writing (retry)",
            "issues": underweight, "agents": agents,
        }

    # ═══════════ Phase 5: Editing — sub-agent returns text ═══════════
    if not (base / "draft" / "v1.md").exists():
        n_files = len(list(sections_dir.glob('*.md')))
        total_sec_wc = sum(word_count(f) for f in sections_dir.glob('*.md'))
        logger.info("Phase 5: Launching Editor — {} section files, total {}w", n_files, total_sec_wc)
        return {
            "action": "launch_single",
            "phase": 5, "phase_name": "Editing",
            "agent": "Editor",
            "prompt": prompt_editor(base),
            "output_file": "draft/v1.md",
            "description": "Merge sections into v1.md",
        }

    draft_wc = word_count(base / "draft" / "v1.md")
    target_words = max_pages * 300
    logger.info("Phase 5 validate: v1.md {}w, target {}w ({}%)",
                draft_wc, target_words, draft_wc * 100 // max(target_words, 1))

    if draft_wc < target_words * 0.4 and can_retry(base, "phase_5_wordcount"):
        logger.warning("Phase 5 RETRY: {}w < 40% of target {}w — deleting v1.md", draft_wc, target_words)
        (base / "draft" / "v1.md").unlink()
        return {
            "action": "launch_single",
            "phase": 5, "phase_name": "Editing (retry)",
            "agent": "Editor",
            "prompt": prompt_editor(base) + f"\nCRITICAL: Target ~{target_words} words. Do NOT lose content.",
            "output_file": "draft/v1.md",
            "description": "Retry merge",
        }

    # ═══════════ Phase 6: Review — sub-agent returns text ═══════════
    review_file = base / "draft" / "_review.md"
    if not review_file.exists():
        logger.info("Phase 6: Launching Critic — draft {}w, target {}w", draft_wc, target_words)
        return {
            "action": "launch_single",
            "phase": 6, "phase_name": "Review",
            "agent": "Critic",
            "prompt": prompt_critic(base, max_pages),
            "output_file": "draft/_review.md",
            "description": "Review draft",
            "info": {"draft_words": draft_wc, "target_words": target_words},
        }

    # ── Handle Verdict ──
    verdict = parse_verdict(base)
    logger.info("Phase 6 verdict={}, revisions={}", verdict, revision_count(base))
    if verdict == "REVISE":
        rev_count = revision_count(base)
        if rev_count < 2:
            shutil.copy(review_file, base / "draft" / f"_review_v{rev_count + 1}.md")
            review_file.unlink()
            (base / "draft" / "v1.md").unlink(missing_ok=True)
            for f in (base / "draft" / "_sections").glob("*.md"):
                f.unlink()
            return cmd_next(base_folder)

    # ═══════════ Phase 7: Illustration — ORCHESTRATOR runs PaperBanana ═══════════
    draft_text = (base / "draft" / "v1.md").read_text(encoding='utf-8')
    has_png_refs = bool(re.search(r'!\[.*?\]\(.*?\.png\)', draft_text))
    manifest = base / "illustrations" / "_manifest.md"
    fig_label = "Рис." if "russian" in params.get("language", "russian").lower() else "Fig."
    ill_mode = params.get("illustration mode", "pipeline").strip().lower()

    if not manifest.exists():
        logger.info("Phase 7: Illustration — manifest missing, generating (mode={})", ill_mode)
        if not os.environ.get("OPENAI_API_KEY"):
            logger.warning("Phase 7: OPENAI_API_KEY not set, skipping illustrations")
            return {
                "action": "warning",
                "phase": 7, "phase_name": "Illustration (skipped)",
                "message": "OPENAI_API_KEY not set. Skipping illustrations.",
            }

        placeholders = re.findall(r'<!-- ILLUSTRATION:(.+?)-->', draft_text)
        logger.debug("Phase 7: found {} ILLUSTRATION placeholders in draft", len(placeholders))
        illustrations = []
        for i, ph in enumerate(placeholders, 1):
            desc_m = re.search(r'description="([^"]+)"', ph)
            type_m = re.search(r'type="([^"]+)"', ph)
            desc = desc_m.group(1) if desc_m else f"Technical diagram {i}"
            itype = type_m.group(1) if type_m else "architecture"
            short_desc = desc[:80]
            illustrations.append({
                "index": i, "type": itype, "description": desc,
                "placeholder": f"<!-- ILLUSTRATION:{ph}-->",
                "output_png": f"illustrations/diagram_{i}.png",
                "embed_as": (
                    f"![{fig_label} {i}. {short_desc}](../illustrations/diagram_{i}.png)\n\n"
                    f"*{fig_label} {i}. {short_desc}*"
                ),
            })

        if not illustrations:
            fallback_items = [
                (1, "architecture", "High-level architecture overview"),
                (2, "comparison", "Platform feature comparison"),
                (3, "pipeline", "Execution flow pipeline"),
            ]
            illustrations = [
                {"index": idx, "type": itype, "description": desc,
                 "output_png": f"illustrations/diagram_{idx}.png",
                 "embed_as": (
                     f"![{fig_label} {idx}. {desc}](../illustrations/diagram_{idx}.png)\n\n"
                     f"*{fig_label} {idx}. {desc}*"
                 )}
                for idx, itype, desc in fallback_items
            ]

        direct_flag = ' --direct' if ill_mode == 'direct' else ''
        return {
            "action": "orchestrator_illustrate",
            "phase": 7, "phase_name": "Illustration",
            "count": len(illustrations),
            "illustrations": illustrations,
            "fig_label": fig_label,
            "draft_file": "draft/v1.md",
            "instructions": (
                "For each illustration:\n"
                "1. Run: python3 .github/skills/image-generator/scripts/"
                f"paperbanana_generate.py \"[description]\" "
                f"\"BASE_FOLDER/[output_png]\"{direct_flag}"
                + (" --context \"[200-500 words section text]\" --critic-rounds 2\n" if ill_mode != 'direct' else "\n")
                + "   Use run_in_terminal with timeout=0 (no limit, pipeline takes 3-5 min)\n"
                "2. Embed in draft/v1.md: replace placeholder with embed_as (image + caption)\n"
                "3. Write manifest to illustrations/_manifest.md\n"
                "4. VERIFY: grep '.png' in v1.md — must find refs"
            ),
        }

    pngs = list((base / "illustrations").glob("*.png"))
    if pngs and not has_png_refs and can_retry(base, "phase_7_embed"):
        manifest.unlink()
        return {
            "action": "orchestrator_illustrate",
            "phase": 7, "phase_name": "Illustration (retry — embed)",
            "count": len(pngs),
            "illustrations": [
                {"index": i+1, "output_png": f"illustrations/{p.name}",
                 "embed_as": (
                     f"![{fig_label} {i+1}. {p.stem}](../illustrations/{p.name})\n\n"
                     f"*{fig_label} {i+1}. {p.stem}*"
                 )}
                for i, p in enumerate(pngs)
            ],
            "fig_label": fig_label,
            "draft_file": "draft/v1.md",
            "instructions": "PNGs exist but not in v1.md. Embed them (image + caption). Rewrite manifest.",
        }

    # ═══════════ Phase 8: Delivery ═══════════
    draft_text = (base / "draft" / "v1.md").read_text(encoding='utf-8')
    final_wc = word_count(base / "draft" / "v1.md")
    logger.success("Phase 8: COMPLETE — {}w, ~{:.1f} pages, {} sections, {} illustrations",
                   final_wc, final_wc / 300, len(toc_sections),
                   len(list((base / 'illustrations').glob('*.png'))))
    return {
        "action": "complete",
        "phase": 8, "phase_name": "Delivery",
        "document": str(base / "draft" / "v1.md"),
        "stats": {
            "words": final_wc,
            "pages_approx": round(final_wc / 300, 1),
            "sections": len(toc_sections),
            "extracts": sum(1 for _ in base.glob("research/*/extract_*.md")),
            "illustrations_png": len(list((base / "illustrations").glob("*.png"))),
            "illustrations_embedded": bool(re.search(r'!\[.*?\]\(.*?\.png\)', draft_text)),
            "verdict": parse_verdict(base),
            "revisions": revision_count(base),
        },
    }


def cmd_status(base_folder: str) -> dict:
    base = Path(base_folder).resolve()
    if not base.exists():
        return {"error": f"Folder {base} does not exist"}

    params = parse_params(base)
    subtopic_dirs = get_subtopic_dirs(base)
    sections_dir = base / "draft" / "_sections"
    v1 = base / "draft" / "v1.md"

    status = {
        "folder": str(base),
        "params": {
            "topic": params.get('topic', '?'),
            "max_pages": params.get('max_pages', '?'),
            "subtopics": len(params.get('subtopics', [])),
        },
        "phases": {},
    }

    links_info = {}
    for d in subtopic_dirs:
        links_info[d.name] = count_urls(d / "_links.md")
    status["phases"]["1_research"] = {
        "topics": len(subtopic_dirs),
        "urls_per_topic": links_info,
        "total_urls": sum(links_info.values()),
    }

    extract_info = {}
    for d in subtopic_dirs:
        exts = list(d.glob("extract_*.md"))
        extract_info[d.name] = {
            "count": len(exts),
            "total_words": sum(word_count(e) for e in exts),
        }
    status["phases"]["1_extraction"] = extract_info

    status["phases"]["2_analysis"] = {
        d.name: (d / "_structure.md").exists() for d in subtopic_dirs
    }

    toc = parse_toc_sections(base)
    status["phases"]["3_planning"] = {
        "has_toc": (base / "research" / "_plan" / "toc.md").exists(),
        "sections": len(toc),
        "total_pages": sum(s["pages"] for s in toc) if toc else 0,
    }

    section_info = {}
    total_pl = 0
    for s in toc:
        f = find_section_file(sections_dir, s["num"])
        if f:
            wc = word_count(f)
            pl = f.read_text(encoding='utf-8').count("<!-- ILLUSTRATION:")
            total_pl += pl
            section_info[s["num"]] = {
                "file": f.name, "words": wc, "target": s["words"],
                "pct": round(wc / max(s["words"], 1) * 100),
            }
        else:
            section_info[s["num"]] = {"file": None, "words": 0, "target": s["words"]}
    status["phases"]["4_writing"] = {"sections": section_info, "total_placeholders": total_pl}

    status["phases"]["5_editing"] = {"has_draft": v1.exists(), "words": word_count(v1)}

    status["phases"]["6_review"] = {
        "has_review": (base / "draft" / "_review.md").exists(),
        "verdict": parse_verdict(base),
        "revisions": revision_count(base),
    }

    pngs = list((base / "illustrations").glob("*.png"))
    dt = v1.read_text(encoding='utf-8') if v1.exists() else ""
    status["phases"]["7_illustration"] = {
        "png_files": len(pngs),
        "embedded_refs": len(re.findall(r'!\[.*?\]\(.*?\.png\)', dt)),
        "manifest": (base / "illustrations" / "_manifest.md").exists(),
    }

    status["retries"] = load_retries(base)
    return status


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "Usage: research_pipeline_runner.py <command> [base_folder]",
            "commands": {
                "init [folder]": "Create folder structure",
                "next <folder>": "Get next pipeline action",
                "status <folder>": "Full status report",
            }
        }, indent=2))
        sys.exit(1)

    command = sys.argv[1]

    if command == "init":
        folder = sys.argv[2] if len(sys.argv) >= 3 else f"generated_docs_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        result = cmd_init(folder)
    elif command in ("next", "status"):
        if len(sys.argv) < 3:
            print(json.dumps({"error": f"Usage: research_pipeline_runner.py {command} <base_folder>"}))
            sys.exit(1)
        result = cmd_next(sys.argv[2]) if command == "next" else cmd_status(sys.argv[2])
    else:
        result = {"error": f"Unknown command: {command}"}

    logger.debug("CMD {}: action={}, phase={}", command,
                 result.get("action", result.get("status", "?")),
                 result.get("phase", "-"))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.opt(exception=True).error("Script crash: {}", e)
        print(json.dumps({"action": "error", "message": f"Script error: {e}"}, ensure_ascii=False))
        sys.exit(1)
