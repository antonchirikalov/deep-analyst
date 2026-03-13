#!/usr/bin/env python3
"""
Deterministic Pipeline Runner v2 for deep-analyst research pipeline.

Architecture: Orchestrator handles ALL I/O (search, extract, file writes).
Sub-agents only RETURN text — orchestrator writes it to disk.

Usage:
    python3 .github/scripts/pipeline_runner.py init [base_folder]
    python3 .github/scripts/pipeline_runner.py next <base_folder>
    python3 .github/scripts/pipeline_runner.py status <base_folder>
"""

import json
import sys
import re
import os
import shutil
import logging
import traceback
from pathlib import Path
from datetime import datetime


def _load_dotenv():
    """Auto-load .env from repo root if it exists."""
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, value = line.partition("=")
                    key, value = key.strip(), value.strip()
                    # Strip surrounding quotes from value
                    if value and value[0] in ('"', "'") and value[-1] == value[0]:
                        value = value[1:-1]
                    if key and key not in os.environ:
                        os.environ[key] = value


_load_dotenv()


def setup_logging(base_folder: str = None):
    """Configure logging: stderr + pipeline.log in base_folder. stdout reserved for JSON."""
    handlers = [logging.StreamHandler(sys.stderr)]
    if base_folder:
        os.makedirs(base_folder, exist_ok=True)
        handlers.append(logging.FileHandler(
            os.path.join(base_folder, "pipeline.log"), encoding='utf-8'))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=handlers,
    )


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
    return len(re.findall(r'https?://\S+', path.read_text(encoding='utf-8')))


# Maximum URLs to extract per subtopic (controls Phase 2 context budget)
MAX_URLS_PER_SUBTOPIC = 5


def extract_urls(path: Path, limit: int = MAX_URLS_PER_SUBTOPIC) -> list:
    """Extract URLs from _links.md. Supports: 'N. URL', '- URL', inline URLs. Deduplicates."""
    if not path.exists():
        return []
    seen = set()
    urls = []
    for line in path.read_text(encoding='utf-8').splitlines():
        for m in re.finditer(r'(https?://\S+)', line):
            url = m.group(1).rstrip('.,;)>').strip()
            if url not in seen:
                seen.add(url)
                urls.append(url)
                if len(urls) >= limit:
                    return urls
    return urls


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
    if re.search(r'Verdict.*APPROVED', text, re.IGNORECASE):
        return "APPROVED"
    if re.search(r'Verdict.*REVISE', text, re.IGNORECASE):
        return "REVISE"
    return "UNKNOWN"


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


def can_retry(base: Path, key: str, max_retries: int = 1, reason: str = "") -> bool:
    retries = load_retries(base)
    if "history" not in retries:
        retries["history"] = []
    count = retries.get(key, 0)
    if count >= max_retries:
        logging.warning("Retry limit reached for %s (%d/%d)", key, count, max_retries)
        return False
    retries[key] = count + 1
    retries["history"].append({
        "key": key, "attempt": count + 1,
        "timestamp": datetime.now().isoformat(), "reason": reason,
    })
    save_retries(base, retries)
    logging.info("Retry %d/%d for %s: %s", count + 1, max_retries, key, reason)
    return True


def revision_count(base: Path) -> int:
    return len(list(base.glob("draft/_review_v*.md")))


def check_relevance(text: str, params: dict) -> float:
    """Check if text is relevant to the research topic. Returns 0.0–1.0."""
    topic = params.get('topic', '')
    subtopics = params.get('subtopics', [])
    keywords = set()
    for source in [topic] + subtopics:
        for word in re.findall(r'\b[a-zA-Z\u0400-\u04ff]{4,}\b', source):
            keywords.add(word.lower())
    if not keywords:
        return 1.0
    text_lower = text.lower()
    found = sum(1 for kw in keywords if kw in text_lower)
    return found / len(keywords)


def record_phase_timing(base: Path, phase: int, phase_name: str):
    """Record phase start time. Closes previous open phase."""
    timing_file = base / ".timing.json"
    timing = {}
    if timing_file.exists():
        timing = json.loads(timing_file.read_text())
    now = datetime.now().isoformat()
    phases = timing.get("phases", {})
    # Close previous open phase
    for data in phases.values():
        if "end" not in data:
            data["end"] = now
            start = datetime.fromisoformat(data["start"])
            end = datetime.fromisoformat(now)
            data["duration_s"] = int((end - start).total_seconds())
    # Start new phase
    key = str(phase)
    if key not in phases:
        phases[key] = {"name": phase_name, "start": now}
    timing["phases"] = phases
    timing_file.write_text(json.dumps(timing, indent=2, ensure_ascii=False))


def _with_log(result: dict, base_folder: str) -> dict:
    """Add log_command to pipeline result for workflow-logger integration."""
    phase = result.get("phase")
    phase_name = result.get("phase_name", "")
    action = result.get("action", "")
    if phase is not None and action not in ("error", "warning", "agent_task"):
        agent_map = {
            "orchestrator_search": "Retriever",
            "orchestrator_extract": "Extractor",
            "launch_parallel": (result.get("agents") or [{}])[0].get("name", "Agent"),
            "launch_single": result.get("agent", "Agent"),
            "orchestrator_illustrate": "Illustrator",
            "retry": "Writer",
            "checkpoint": "Orchestrator",
        }
        agent = agent_map.get(action, "Orchestrator")
        if action == "complete":
            stats = result.get("stats", {})
            result["log_command"] = (
                f'python3 .github/skills/workflow-logger/scripts/workflow-logger.py complete '
                f'--folder {base_folder} --words {stats.get("words", 0)} '
                f'--pages {stats.get("pages_approx", 0)} '
                f'--sections {stats.get("sections", 0)}'
            )
        else:
            result["log_command"] = (
                f'python3 .github/skills/workflow-logger/scripts/workflow-logger.py phase '
                f'--folder {base_folder} --phase {phase} --agent {agent} '
                f'--status start --detail "{phase_name}"'
            )
    return result


# ═══════════════════════════════════════════════════════════════
# PROMPT BUILDERS — sub-agents READ files, RETURN text
# Orchestrator writes the returned text to output_file
# ═══════════════════════════════════════════════════════════════

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
        f'4. NO FILLER: Ban "мощный", "инновационный", "comprehensive", "революционный".\n'
        f'5. NO ASCII DIAGRAMS: NEVER use box-drawing characters (┌─┐│└┘├┤═║). '
        f'Use only <!-- ILLUSTRATION: ... --> placeholders for diagrams. '
        f'Text-art diagrams look broken in PDF/web rendering.\n'
        f'6. NO TIMELINES/ROADMAPS: Do NOT invent implementation phases with durations '
        f'("Quick Wins 2-4 недели", "Phase 1: Week 1-2"). Write TECHNICAL ANALYSIS '
        f'of how things work, not project management plans. '
        f'If the user did not ask for a migration roadmap or timeline, DO NOT include one.\n'
        f'7. LANGUAGE: Write in the language from params.md.\n\n'
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
        f'- REMOVE any ASCII/box-drawing diagrams (┌─┐│└┘├┤═║). Replace with <!-- ILLUSTRATION: ... --> placeholder or plain text list.\n'
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
        f'6. ASCII DIAGRAMS: If document contains box-drawing characters (┌─┐│└┘├┤═║) -> REVISE. These MUST be replaced with <!-- ILLUSTRATION: ... --> placeholders or removed.\n'
        f'7. Verdict: ## Verdict: APPROVED or ## Verdict: REVISE\n'
        f'8. If REVISE: list specific sections and issues.\n\n'
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
    return {
        "status": "ready",
        "folder": str(base),
        "next_step": "Write research/_plan/params.md, then run next",
    }


def cmd_next(base_folder: str) -> dict:
    base = Path(base_folder).resolve()
    if not base.exists():
        return {"action": "error", "message": f"Folder {base} does not exist."}

    params = parse_params(base)

    # ── Phase 0 ──
    if not params or not params.get('subtopics'):
        return {
            "action": "agent_task", "phase": 0,
            "phase_name": "Decomposition",
            "message": "Write research/_plan/params.md with Topic, Max pages, Subtopics.",
        }

    main_topic = params.get('topic', 'Research')
    max_pages = params.get('max_pages', 25)
    subtopics = params['subtopics']

    for st in subtopics:
        slug = slugify(st)
        (base / "research" / slug).mkdir(parents=True, exist_ok=True)

    subtopic_dirs = get_subtopic_dirs(base)

    # ═══════════ Phase 1: Retrieval — ORCHESTRATOR searches ═══════════
    missing_links = [d for d in subtopic_dirs if not (d / "_links.md").exists()]
    if missing_links:
        searches = []
        for d in missing_links:
            name = d.name.replace('_', ' ')
            searches.append({
                "query": f"{name} architecture implementation internals source code API",
                "query_alt": f"{name} engineering blog deep dive specification protocol",
                "subtopic": d.name,
                "output_file": str((d / "_links.md").relative_to(base)),
            })
        return {
            "action": "orchestrator_search",
            "phase": 1, "phase_name": "Retrieval",
            "count": len(searches),
            "searches": searches,
            "instructions": (
                "For EACH search: call tavily_search(query, max_results=5). "
                "Format results as numbered list: 'N. URL — Title'. "
                "Write to output_file in BASE_FOLDER. "
                "If tavily fails, try query_alt. "
                "If both fail, use fetch_webpage on known documentation URLs."
            ),
        }

    # ── Validate Phase 1 ──
    weak_links = []
    for d in subtopic_dirs:
        if count_urls(d / "_links.md") < 3:
            weak_links.append({
                "subtopic": d.name,
                "urls": count_urls(d / "_links.md"),
                "output_file": str((d / "_links.md").relative_to(base)),
            })
    if weak_links and can_retry(base, "phase_1_urls",
            reason=f"{len(weak_links)} subtopics with <3 URLs"):
        return {
            "action": "orchestrator_search",
            "phase": 1, "phase_name": "Retrieval (retry)",
            "count": len(weak_links),
            "searches": [{
                "query": f"{w['subtopic'].replace('_', ' ')} official documentation API reference",
                "query_alt": f"{w['subtopic'].replace('_', ' ')} source code internals how it works",
                "subtopic": w["subtopic"],
                "output_file": w["output_file"],
                "append": True,
            } for w in weak_links],
            "instructions": "RETRY: Too few URLs. Broaden queries. Append to existing file.",
        }

    # ═══════════ Phase 2: Extraction — ORCHESTRATOR extracts ═══════════
    missing_extracts = [d for d in subtopic_dirs if not list(d.glob("extract_*.md"))]
    if missing_extracts:
        extractions = []
        for d in missing_extracts:
            urls = extract_urls(d / "_links.md")
            for i, url in enumerate(urls, 1):
                extractions.append({
                    "url": url,
                    "subtopic": d.name,
                    "index": i,
                    "output_file": str((d / f"extract_{i}.md").relative_to(base)),
                })
        return {
            "action": "orchestrator_extract",
            "phase": 2, "phase_name": "Extraction",
            "count": len(extractions),
            "extractions": extractions,
            "instructions": (
                "For EACH URL: call tavily_extract(urls=[url]) or fetch_webpage(url). "
                "Write FULL content to output_file with header:\n"
                "# Extract: [title]\nSource: [url]\nWords: ~N\n\n[content]\n"
                "Do NOT summarize. Copy verbatim. MINIMUM 1500 words per extract. "
                "MUST include ALL code blocks, JSON schemas, CLI commands, "
                "API examples, directory structures, config formats from the source. "
                "KEEP SOURCE LANGUAGE (English if source is English). "
                "Do NOT translate during extraction. Skip failed URLs."
            ),
        }

    # ── Validate Phase 2 ──
    extract_issues = []
    for d in subtopic_dirs:
        exts = list(d.glob("extract_*.md"))
        urls = count_urls(d / "_links.md")
        n_ext = len(exts)
        # Count non-empty extracts (0-byte files don't count)
        real_exts = [e for e in exts if word_count(e) > 50]
        n_real = len(real_exts)
        avg_wc = sum(word_count(e) for e in exts) / max(n_ext, 1)
        if n_real < max(int(urls * 0.4), 2) and n_real < 3:
            extract_issues.append({
                "subtopic": d.name, "extracts": n_real, "urls": urls,
                "avg_words": int(avg_wc), "issue": f"Only {n_real} non-empty from {urls} URLs",
            })
        elif avg_wc < 800:
            extract_issues.append({
                "subtopic": d.name, "extracts": n_ext, "urls": urls,
                "avg_words": int(avg_wc), "issue": f"Too shallow (avg {int(avg_wc)} words, need 800+)",
            })

    if extract_issues and can_retry(base, "phase_2_quality", max_retries=2,
            reason="; ".join(f"{i['subtopic']}: {i['issue']}" for i in extract_issues)):
        extractions = []
        for issue in extract_issues:
            d = base / "research" / issue["subtopic"]
            urls = extract_urls(d / "_links.md")
            existing = len(list(d.glob("extract_*.md")))
            for i, url in enumerate(urls[existing:], existing + 1):
                extractions.append({
                    "url": url, "subtopic": issue["subtopic"],
                    "index": i,
                    "output_file": str((d / f"extract_{i}.md").relative_to(base)),
                })
        if extractions:
            return {
                "action": "orchestrator_extract",
                "phase": 2, "phase_name": "Extraction (retry)",
                "count": len(extractions),
                "extractions": extractions,
                "issues": extract_issues,
                "instructions": "RETRY: Extract remaining URLs. Copy verbatim.",
            }

    # ═══════════ Phase 3: Analysis — sub-agent returns text ═══════════
    missing_structures = [d for d in subtopic_dirs if not (d / "_structure.md").exists()]
    if missing_structures:
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
            "phase": 3, "phase_name": "Analysis",
            "agent_count": len(agents), "agents": agents,
        }

    # ═══════════ Phase 4: Planning — sub-agent returns text ═══════════
    if not (base / "research" / "_plan" / "toc.md").exists():
        return {
            "action": "launch_single",
            "phase": 4, "phase_name": "Planning",
            "agent": "Planner",
            "prompt": prompt_planner(base),
            "output_file": "research/_plan/toc.md",
            "description": "Build unified ToC",
        }

    # ── Validate Phase 4 ──
    toc_sections = parse_toc_sections(base)
    if not toc_sections:
        if can_retry(base, "phase_4_parse", reason="ToC unparseable"):
            (base / "research" / "_plan" / "toc.md").unlink()
            return {
                "action": "launch_single",
                "phase": 4, "phase_name": "Planning (retry)",
                "agent": "Planner",
                "prompt": prompt_planner(base) + (
                    "\nRETRY: Previous ToC unparseable. "
                    "Use EXACTLY: ## NN. Title — Pages: N — Sources: path1, path2"
                ),
                "output_file": "research/_plan/toc.md",
                "description": "Retry ToC",
            }
        return {"action": "error", "message": "ToC unparseable."}

    # ═══════════ Phase 5: Writing — sub-agents return text ═══════════
    sections_dir = base / "draft" / "_sections"
    missing_sections = []
    for s in toc_sections:
        if not find_section_file(sections_dir, s["num"]):
            missing_sections.append(s)

    is_rev = revision_count(base) > 0

    if missing_sections:
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
            "phase": 5, "phase_name": "Writing" + (" (revision)" if is_rev else ""),
            "agent_count": len(agents), "agents": agents,
        }

    # ── Validate Phase 5 ──
    underweight = []
    for s in toc_sections:
        f = find_section_file(sections_dir, s["num"])
        if f and word_count(f) < s["words"] * 0.5:
            underweight.append({
                "section": f"{s['num']}. {s['title']}",
                "actual": word_count(f), "target": s["words"],
            })

    if underweight and can_retry(base, "phase_5_wordcount",
            reason="; ".join(f"{u['section']}: {u['actual']}/{u['target']}w" for u in underweight)):
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
            "phase": 5, "phase_name": "Writing (retry)",
            "issues": underweight, "agents": agents,
        }

    # ── Validate Phase 5: Relevance ──
    irrelevant = []
    for s in toc_sections:
        f = find_section_file(sections_dir, s["num"])
        if f:
            text = f.read_text(encoding='utf-8')
            score = check_relevance(text, params)
            if score < 0.15:
                irrelevant.append({
                    "section": f"{s['num']}. {s['title']}",
                    "relevance": round(score, 2),
                })
                logging.warning("Low relevance %.2f in section %s", score, s["num"])

    if irrelevant and can_retry(base, "phase_5_relevance",
            reason="; ".join(f"{i['section']}: rel={i['relevance']}" for i in irrelevant)):
        agents = []
        for ir in irrelevant:
            s = next(x for x in toc_sections if x["num"] == ir["section"][:2])
            bad = find_section_file(sections_dir, s["num"])
            if bad:
                bad.unlink()
            agents.append({
                "name": "Writer",
                "prompt": prompt_writer(base, s, is_revision=is_rev) +
                    f"\nCRITICAL RETRY: Previous content was OFF-TOPIC (relevance={ir['relevance']}). "
                    f"Write ONLY about {main_topic}. Use ONLY source extracts.",
                "output_file": f"draft/_sections/{s['filename']}",
                "description": f"Retry (off-topic) section {s['num']}",
            })
        return {
            "action": "retry",
            "phase": 5, "phase_name": "Writing (retry — off-topic)",
            "issues": irrelevant, "agents": agents,
        }

    # ═══════════ Phase 6: Editing — sub-agent returns text ═══════════
    if not (base / "draft" / "v1.md").exists():
        return {
            "action": "launch_single",
            "phase": 6, "phase_name": "Editing",
            "agent": "Editor",
            "prompt": prompt_editor(base),
            "output_file": "draft/v1.md",
            "description": "Merge sections into v1.md",
        }

    draft_wc = word_count(base / "draft" / "v1.md")
    target_words = max_pages * 300

    if draft_wc < target_words * 0.4 and can_retry(base, "phase_6_wordcount",
            reason=f"Draft {draft_wc}w < 40% of target {target_words}w"):
        (base / "draft" / "v1.md").unlink()
        return {
            "action": "launch_single",
            "phase": 6, "phase_name": "Editing (retry)",
            "agent": "Editor",
            "prompt": prompt_editor(base) + f"\nCRITICAL: Target ~{target_words} words. Do NOT lose content.",
            "output_file": "draft/v1.md",
            "description": "Retry merge",
        }

    # ═══════════ Phase 7: Review — sub-agent returns text ═══════════
    review_file = base / "draft" / "_review.md"
    if not review_file.exists():
        return {
            "action": "launch_single",
            "phase": 7, "phase_name": "Review",
            "agent": "Critic",
            "prompt": prompt_critic(base, max_pages),
            "output_file": "draft/_review.md",
            "description": "Review draft",
            "info": {"draft_words": draft_wc, "target_words": target_words},
        }

    # ── Handle Verdict ──
    verdict = parse_verdict(base)
    if verdict == "REVISE":
        rev_count = revision_count(base)
        if rev_count < 2:
            shutil.copy(review_file, base / "draft" / f"_review_v{rev_count + 1}.md")
            review_file.unlink()
            (base / "draft" / "v1.md").unlink(missing_ok=True)
            for f in (base / "draft" / "_sections").glob("*.md"):
                f.unlink()
            return cmd_next(base_folder)

    # ═══════════ Phase 8: Illustration — ORCHESTRATOR runs PaperBanana ═══════════
    # Find the draft file — check standard path first, then fallback to root-level
    draft_path = base / "draft" / "v1.md"
    if not draft_path.exists():
        # Fallback: final_article.md at root (from non-pipeline runs)
        alt_path = base / "final_article.md"
        if alt_path.exists():
            draft_path = alt_path
    if not draft_path.exists():
        return {"action": "error", "message": f"No draft found at draft/v1.md or final_article.md"}

    draft_text = draft_path.read_text(encoding='utf-8')
    has_png_refs = bool(re.search(r'!\[.*?\]\(.*?\.png\)', draft_text))
    manifest = base / "illustrations" / "_manifest.md"

    if not manifest.exists():
        if not os.environ.get("OPENAI_API_KEY"):
            return {
                "action": "warning",
                "phase": 8, "phase_name": "Illustration (skipped)",
                "message": "OPENAI_API_KEY not set. Skipping illustrations.",
            }

        placeholders = re.findall(r'<!-- ILLUSTRATION:(.+?)-->', draft_text)
        illustrations = []
        for i, ph in enumerate(placeholders, 1):
            desc_m = re.search(r'description="([^"]+)"', ph)
            type_m = re.search(r'type="([^"]+)"', ph)
            desc = desc_m.group(1) if desc_m else f"Technical diagram {i}"
            itype = type_m.group(1) if type_m else "architecture"
            illustrations.append({
                "index": i, "type": itype, "description": desc,
                "placeholder": f"<!-- ILLUSTRATION:{ph}-->",
                "output_png": f"illustrations/diagram_{i}.png",
                "embed_as": f"![Рис. {i}. {desc[:60]}](../illustrations/diagram_{i}.png)",
            })

        if not illustrations:
            illustrations = [
                {"index": 1, "type": "architecture",
                 "description": "High-level architecture overview",
                 "output_png": "illustrations/diagram_1.png",
                 "embed_as": "![Рис. 1](../illustrations/diagram_1.png)"},
                {"index": 2, "type": "comparison",
                 "description": "Platform feature comparison",
                 "output_png": "illustrations/diagram_2.png",
                 "embed_as": "![Рис. 2](../illustrations/diagram_2.png)"},
                {"index": 3, "type": "pipeline",
                 "description": "Execution flow pipeline",
                 "output_png": "illustrations/diagram_3.png",
                 "embed_as": "![Рис. 3](../illustrations/diagram_3.png)"},
            ]

        draft_relpath = str(draft_path.relative_to(base))
        return {
            "action": "orchestrator_illustrate",
            "phase": 8, "phase_name": "Illustration",
            "count": len(illustrations),
            "illustrations": illustrations,
            "draft_file": draft_relpath,
            "instructions": (
                f"For each illustration:\n"
                f"1. Run: python3 .github/skills/image-generator/scripts/"
                f"paperbanana_generate.py \"[short 2-4 sentence prompt]\" "
                f"\"BASE_FOLDER/[output_png]\" --direct\n"
                f"2. Embed PNG in {draft_relpath} (replace placeholder or insert near section)\n"
                f"3. Write manifest to illustrations/_manifest.md\n"
                f"4. VERIFY: grep '.png' in {draft_relpath} — must find refs"
            ),
        }

    pngs = list((base / "illustrations").glob("*.png"))
    if pngs and not has_png_refs and can_retry(base, "phase_8_embed",
            reason=f"{len(pngs)} PNGs exist but not embedded in draft"):
        manifest.unlink()
        draft_relpath = str(draft_path.relative_to(base))
        return {
            "action": "orchestrator_illustrate",
            "phase": 8, "phase_name": "Illustration (retry — embed)",
            "count": len(pngs),
            "illustrations": [
                {"index": i+1, "output_png": f"illustrations/{p.name}",
                 "embed_as": f"![Рис. {i+1}](../illustrations/{p.name})"}
                for i, p in enumerate(pngs)
            ],
            "draft_file": draft_relpath,
            "instructions": f"PNGs exist but not in {draft_relpath}. Embed them. Rewrite manifest.",
        }

    # ═══════════ Phase 9: Delivery ═══════════
    final_wc = word_count(draft_path)
    return {
        "action": "complete",
        "phase": 9, "phase_name": "Delivery",
        "document": str(draft_path),
        "stats": {
            "words": final_wc,
            "pages_approx": round(final_wc / 300, 1),
            "sections": len(toc_sections),
            "extracts": sum(1 for _ in base.glob("research/*/extract_*.md")),
            "illustrations_png": len(list((base / "illustrations").glob("*.png"))),
            "illustrations_embedded": bool(re.search(r'!\[.*?\]\(.*?\.png\)', draft_path.read_text(encoding='utf-8'))),
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
    if not v1.exists():
        alt = base / "final_article.md"
        if alt.exists():
            v1 = alt

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
    status["phases"]["1_retrieval"] = {
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
    status["phases"]["2_extraction"] = extract_info

    status["phases"]["3_analysis"] = {
        d.name: (d / "_structure.md").exists() for d in subtopic_dirs
    }

    toc = parse_toc_sections(base)
    status["phases"]["4_planning"] = {
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
    status["phases"]["5_writing"] = {"sections": section_info, "total_placeholders": total_pl}

    status["phases"]["6_editing"] = {"has_draft": v1.exists(), "words": word_count(v1)}

    status["phases"]["7_review"] = {
        "has_review": (base / "draft" / "_review.md").exists(),
        "verdict": parse_verdict(base),
        "revisions": revision_count(base),
    }

    pngs = list((base / "illustrations").glob("*.png"))
    dt = v1.read_text(encoding='utf-8') if v1.exists() else ""
    status["phases"]["8_illustration"] = {
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
            "error": "Usage: pipeline_runner.py <command> [base_folder]",
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
        setup_logging(folder)
        result = cmd_init(folder)
    elif command in ("next", "status"):
        if len(sys.argv) < 3:
            print(json.dumps({"error": f"Usage: pipeline_runner.py {command} <base_folder>"}))
            sys.exit(1)
        setup_logging(sys.argv[2])
        logging.info("cmd=%s folder=%s", command, sys.argv[2])
        if command == "next":
            result = cmd_next(sys.argv[2])
            # R7: record phase timing
            phase = result.get("phase")
            if phase is not None:
                record_phase_timing(Path(sys.argv[2]).resolve(), phase, result.get("phase_name", ""))
            # R2: add log_command for workflow-logger
            result = _with_log(result, sys.argv[2])
        else:
            result = cmd_status(sys.argv[2])
    else:
        setup_logging()
        result = {"error": f"Unknown command: {command}"}

    logging.info("Result: action=%s phase=%s", result.get("action"), result.get("phase"))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        tb = traceback.format_exc()
        logging.error("Pipeline error: %s\n%s", e, tb)
        print(json.dumps({
            "action": "error",
            "message": f"Script error: {e}",
            "traceback": tb,
        }, ensure_ascii=False))
        sys.exit(1)
