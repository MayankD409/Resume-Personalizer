"""
Utilities for locating, activating, or de‑activating *Project* blocks in the
LaTeX resume template (Jake Gutierrez style) used by Me.

A "block" starts at a line with \resumeProjectHeading (possibly commented out)
and ends just *before* the next heading or the end of the Projects section.
"""

from __future__ import annotations
from typing import List, Dict
import re

# ------------------------- regex patterns -------------------------
# Simplified regex approach
HEADING_RE = re.compile(r"\\resumeProjectHeading")
RESUME_ITEM_RE = re.compile(r"\\resumeItem\{(.*?)\}")

PROJECTS_SECTION_START = re.compile(r"^\\section\{Projects\}")
SECTION_RE = re.compile(r"^\\section\{") # any new section

# Print all lines in the file
def print_file_lines(lines: List[str]) -> None:
    """Debug function to print all lines in the file with line numbers."""
    print("\nDEBUG: File contents:")
    for i, line in enumerate(lines):
        print(f"{i+1:3d}: {line}")
    print("\n")

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
      * content – list of bullet points from resumeItem tags
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
            i += 1
            continue

        # If we hit a *new* \section{...} that is not a "Projects", we're done
        if inside_projects and SECTION_RE.match(line) \
            and not PROJECTS_SECTION_START.match(line):
            break # end of Projects section
        
        # Found a project heading (active or commented)
        if HEADING_RE.search(line):
            start_idx = i
            active = not line.lstrip().startswith("%") # Check if the line is commented using lstrip() which removes leading spaces.

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
            
            # Collect bullet points content
            content = []
            
            # Find the end of this block
            next_heading_idx = i + 1
            while next_heading_idx < n:
                if HEADING_RE.search(lines[next_heading_idx]) or \
                   (SECTION_RE.match(lines[next_heading_idx]) and not PROJECTS_SECTION_START.match(lines[next_heading_idx])):
                    break
                next_heading_idx += 1
            
            # Scan through this block looking for resumeItem
            for j in range(i, next_heading_idx):
                line_to_check = lines[j]
                # Remove comment if present
                if line_to_check.lstrip().startswith("%"):
                    line_to_check = line_to_check.lstrip()[1:].lstrip()
                
                # Look for resumeItem
                if "\\resumeItem{" in line_to_check:
                    # Extract content
                    start_brace = line_to_check.find("\\resumeItem{") + len("\\resumeItem{")
                    open_braces = 1
                    end_brace = start_brace
                    
                    while end_brace < len(line_to_check) and open_braces > 0:
                        if line_to_check[end_brace] == '{':
                            open_braces += 1
                        elif line_to_check[end_brace] == '}':
                            open_braces -= 1
                        end_brace += 1
                    
                    if open_braces == 0:
                        bullet_content = line_to_check[start_brace:end_brace-1]
                        content.append(bullet_content)
            
            # Move forward to the next project heading or section
            i = next_heading_idx
            
            blocks.append({
                "start": start_idx,
                "end": i,
                "active": active,
                "title": title,
                "content": content
            })
        else:
            i += 1
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

# --------------- quick CLI debug helper ---------------- # Uncomment below to run as a script and run using this command: python3 -m latex_parser <resume.tex>
if __name__ == "__main__":
    import pathlib, sys
    print("LaTeX Parser CLI")
    tex_path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if not tex_path or not tex_path.exists():
        print("usage: python3 -m latex_parser <resume.tex>")
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
        
        # Print bullet points content
        if b["content"]:
            print(f"    Bullet Points ({len(b['content'])})")
            for bullet_idx, bullet in enumerate(b["content"], 1):
                # Truncate long bullets for display
                truncated = bullet[:70] + ("..." if len(bullet) > 70 else "")
                print(f"      {bullet_idx}. {truncated}")
        else:
            print("    No bullet points found")
        
        # Uncomment next line if you want to see line numbers 
        # print(f"    Lines {b['start']+1} to {b['end']}")