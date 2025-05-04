"""
Utilities for locating, activating, or de‑activating *Project* blocks in the
LaTeX resume template (Jake Gutierrez style) used by Mayank.

A "block" starts at a line with \resumeProjectHeading (possibly commented out)
and ends just *before* the next heading or the end of the Projects section.
"""

from __future__ import annotations
from typing import List, Dict
import re

# ------------------------- regex patterns -------------------------
# Simplified regex approach
HEADING_RE = re.compile(r"\\resumeProjectHeading")

PROJECTS_SECTION_START = re.compile(r"^\\section\{Projects\}")
SECTION_RE = re.compile(r"^\\section\{") # any new section

# --------------- core functions ---------------- #
def extract_project_blocks(lines: List[str]) -> List[Dict]:
    """
    Scan the LaTeX source (as a list of lines) and return metadata for every
    project block.

    Each dict contains:
      * start   – index of first line of block
      * end     – index of line *after* the block (Python slice‑style)
      * active  – bool, False if heading is commented
      * title   – plain‑text title of the project (best‑effort)
    """
    blocks: List[Dict] = []
    inside_projects = False
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]

        # Detect the "Projects" Section start so we ignore headings elsewhere
        if PROJECTS_SECTION_START.match(line):
            inside_projects = True
        
        if not inside_projects:
            i+=1
            continue

        # If we hit a *new* \section{...} that is not a "Projects", we're done
        if inside_projects and SECTION_RE.match(line) \
            and not PROJECTS_SECTION_START.match(line):
            break # end of Projects section
        
        # Found a project heading (active or commented)
        if HEADING_RE.search(line):
            start_idx = i
            active = not line.lstrip().startswith("%")

            # Extract project title for convenience - look at next line if needed
            title = "<unknown>"
            # Try to extract from current line first
            title_match = re.search(r"\\textbf\{([^}]*)\}", line)
            if title_match:
                title = title_match.group(1)
            # If not found and there's a next line, try that
            elif i+1 < n and "\\textbf" in lines[i+1]:
                title_match = re.search(r"\\textbf\{([^}]*)\}", lines[i+1])
                if title_match:
                    title = title_match.group(1)
            
            # Move forward until *next* heading or end of Projects section
            i+=1
            while i < n and not HEADING_RE.search(lines[i]) \
                and not (SECTION_RE.match(lines[i]) and 
                          not PROJECTS_SECTION_START.match(lines[i])):
                i+=1
            
            blocks.append({
                "start": start_idx,
                "end": i,
                "active": active,
                "title": title,
            })
        else:
            i+=1
    return blocks

# ------------------------- toggle functions -------------------------

def toggle_block(lines: List[str], block: Dict, activate: bool = True) -> None:
    """
    Comment or uncomment *in‑place* all lines in the given block dict.

    Args
    ----
    lines     : list[str] – full LaTeX file splitlines()
    block     : dict      – one element from extract_project_blocks()
    activate  : bool      – True  ➜ remove '%' (uncomment)
                            False ➜ add '%'    (comment)
    """
    for j in range(block["start"], block["end"]):
        stripped = lines[j].lstrip()
        if activate:
            # Remove leading % if present
            if stripped.startswith("%"):
                lines[j] = stripped[1:]
        else:
            # comment out line
            if not stripped.startswith("%"):
                lines[j] = "% " + lines[j]

# --------------- quick CLI debug helper ---------------- #
if __name__ == "__main__":
    import pathlib, sys
    print("LaTeX Parser CLI")
    tex_path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if not tex_path or not tex_path.exists():
        print("usage: python -m latex_parser <resume.tex>")
        sys.exit(1)

    content = tex_path.read_text(encoding="utf-8").splitlines()
    blocks = extract_project_blocks(content)
    
    if len(blocks) == 0:
        print("Warning: No project blocks were found! Check if the file has a Projects section with \\resumeProjectHeading entries.")
    else:
        print(f"Found {len(blocks)} project blocks in {tex_path.name}")
        print("-" * 70)
        
        # Count active vs inactive
        active_count = sum(1 for b in blocks if b["active"])
        inactive_count = len(blocks) - active_count
        print(f"Active: {active_count}, Commented-out: {inactive_count}")
        print("-" * 70)
    
    for idx, b in enumerate(blocks, 1):
        status = "ACTIVE" if b["active"] else "commented‑out"
        print(f"{idx:02d}. {b['title'][:60]:60}  → {status}")
        # Uncomment next line if you want to see line numbers 
        # print(f"    Lines {b['start']+1} to {b['end']}")