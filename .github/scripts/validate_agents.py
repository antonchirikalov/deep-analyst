#!/usr/bin/env python3
"""Validate all agent and instruction files for structural correctness."""

import os
import sys
import re

AGENTS_DIR = ".github/agents"
INSTRUCTIONS_DIR = ".github/instructions"

def parse_frontmatter(content):
    """Extract YAML-like frontmatter from markdown."""
    # Handle ```chatagent or ```instructions wrapper
    if content.startswith("````chatagent") or content.startswith("````instructions") or content.startswith("```instructions"):
        idx = content.index("---")
        content = content[idx:]
    if not content.startswith("---"):
        return None, "no YAML frontmatter"
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None, "malformed frontmatter (no closing ---)"
    fm_text = parts[1].strip()
    fm = {}
    for line in fm_text.split("\n"):
        if ":" in line:
            key, val = line.split(":", 1)
            fm[key.strip()] = val.strip()
    return fm, None

def validate_agents():
    errors = []
    agents = {}
    
    for f in sorted(os.listdir(AGENTS_DIR)):
        if not f.endswith(".agent.md"):
            continue
        path = os.path.join(AGENTS_DIR, f)
        with open(path) as fh:
            content = fh.read()
        
        fm, err = parse_frontmatter(content)
        if err:
            errors.append(f"{f}: {err}")
            continue
        
        name = fm.get("name", "").strip("'\"")
        model = fm.get("model", "").strip("'\"")
        tools_raw = fm.get("tools", "")
        ui = fm.get("user-invocable", "")
        agents_raw = fm.get("agents", "")
        
        # Parse tools list
        tools = re.findall(r"'([^']+)'", tools_raw)
        agents_list = re.findall(r"'([^']+)'", agents_raw) if agents_raw else []
        
        if not name:
            errors.append(f"{f}: missing name")
        if not model:
            errors.append(f"{f}: missing model")
        if not tools:
            errors.append(f"{f}: missing/empty tools")
        
        # Check run_in_terminal if agent has trace sections
        has_trace = "agent-trace.py" in content
        has_terminal = "run_in_terminal" in tools_raw
        if has_trace and not has_terminal:
            errors.append(f"{f}: has agent-trace.py calls but no run_in_terminal in tools")
        
        agents[name] = {
            "file": f,
            "model": model,
            "tools": tools,
            "user_invocable": ui,
            "agents": agents_list,
        }
        print(f"  ✓ {f}: name={name}, model={model}, tools={len(tools)}, user-invocable={ui or 'default'}")
    
    return agents, errors

def validate_instructions():
    errors = []
    instructions = []
    
    for root, dirs, files in os.walk(INSTRUCTIONS_DIR):
        for f in sorted(files):
            if not f.endswith(".instructions.md"):
                continue
            path = os.path.join(root, f)
            rel = os.path.relpath(path, ".github")
            with open(path) as fh:
                content = fh.read()
            
            fm, err = parse_frontmatter(content)
            if err:
                errors.append(f"{rel}: {err}")
                continue
            
            desc = fm.get("description", "")
            if not desc:
                errors.append(f"{rel}: missing description in frontmatter")
            
            instructions.append(rel)
            print(f"  ✓ {rel}")
    
    return instructions, errors

def validate_cross_refs(agents_dict):
    errors = []
    
    # Check Orchestrator's agents list matches actual agent names
    orch = agents_dict.get("Research Orchestrator")
    if orch:
        for agent_name in orch["agents"]:
            if agent_name not in agents_dict:
                errors.append(f"Orchestrator references agent '{agent_name}' but no agent with that name exists")
    
    # Check instruction file references in agents
    for name, info in agents_dict.items():
        path = os.path.join(AGENTS_DIR, info["file"])
        with open(path) as fh:
            content = fh.read()
        
        # Find instruction references
        refs = re.findall(r"\.\./instructions/([^\)]+)", content)
        for ref in refs:
            full_path = os.path.join(".github/instructions", ref)
            if not os.path.exists(full_path):
                errors.append(f"{info['file']}: references missing instruction file: {ref}")
    
    return errors

def validate_phase_numbers(agents_dict):
    # Phase numbers for agents that have --phase in trace calls.
    # Shared agents (Planner, Writer, Editor, Critic, Illustrator) use
    # architecture pipeline phase numbers. Analyst is research-only (Phase 2).
    # Researcher has no trace calls (no --phase).
    expected = {
        "Research Orchestrator": "0",
        "Analyst": "2",
        "Planner": "4",
        "Writer": "5",
        "Editor": "6",
        "Critic": "7",
        "Illustrator": "8",
        "PDF Exporter": "9",
    }
    errors = []
    
    for name, info in agents_dict.items():
        path = os.path.join(AGENTS_DIR, info["file"])
        with open(path) as fh:
            content = fh.read()
        
        phases = re.findall(r"--phase (\d+)", content)
        if not phases:
            continue
        
        exp = expected.get(name)
        if exp and phases[0] != exp:
            errors.append(f"{info['file']}: first --phase is {phases[0]}, expected {exp}")
        
        # Check all phases in file are consistent
        unique = set(phases)
        if name != "Research Orchestrator" and len(unique) > 1:
            errors.append(f"{info['file']}: uses multiple phase numbers: {unique}")
    
    return errors

def main():
    all_errors = []
    
    print("=== Agent Files ===")
    agents, errs = validate_agents()
    all_errors.extend(errs)
    
    print(f"\n=== Instruction Files ===")
    instructions, errs = validate_instructions()
    all_errors.extend(errs)
    
    print(f"\n=== Cross-Reference Check ===")
    errs = validate_cross_refs(agents)
    all_errors.extend(errs)
    if not errs:
        print("  ✓ All instruction file references resolve correctly")
        print("  ✓ All Orchestrator agent references match actual agents")
    
    print(f"\n=== Phase Number Check ===")
    errs = validate_phase_numbers(agents)
    all_errors.extend(errs)
    if not errs:
        print("  ✓ All phase numbers consistent with plan")
    
    print(f"\n{'='*50}")
    if all_errors:
        print(f"✗ {len(all_errors)} error(s) found:")
        for e in all_errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print(f"✓ All {len(agents)} agents + {len(instructions)} instructions valid")
        sys.exit(0)

if __name__ == "__main__":
    main()
