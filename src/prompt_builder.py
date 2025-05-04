# ──────────────────────────────────────────────────────────────
# src/prompt_builder.py
# Build chat messages for the TWO‑PASS LLM pipeline.
# ──────────────────────────────────────────────────────────────
from __future__ import annotations
import re
from typing import List, Dict, Optional
from src.prompt_improver import enhance_project_selection_prompt, enhance_bullet_rewrite_prompt, create_examples_for_bullets

# ---------- rough token counter ------------------------------------------ #
def approx_tokens(text: str) -> int:
    """Very rough: 1 token ≈ 3.7 chars for LaTeX‑heavy text."""
    return int(len(text) / 3.7) + 1


TOKEN_LIMIT   = 128_000              # GPT‑4o / Gemini‑1.5
SAFETY_MARGIN = int(TOKEN_LIMIT * 0.9)

# ---------- résumé compressor (drop comments, squash whitespace) ---------- #
COMMENT_RE    = re.compile(r"^\s*%")
WHITESPACE_RE = re.compile(r"\s+")

def compress_resume(tex: str) -> str:
    lines = [l for l in tex.splitlines() if not COMMENT_RE.match(l)]
    return WHITESPACE_RE.sub(" ", " ".join(lines)).strip()

# ---------- PASS‑1 prompt: choose projects -------------------------------- #
SYSTEM_P1 = """\
You are a résumé‑tailor assistant specializing in optimizing resumes for specific job applications.

Return ONLY valid JSON with keys:
  include_projects : list[str]  # project titles to uncomment
  exclude_projects : list[str]  # project titles to comment

Do NOT rewrite bullets yet.
"""

def build_messages_pass1(
        jd_text: str,
        role: str,
        company: str,
        resume_tex: list[str] or str,
        projects: Optional[List[Dict]] = None
) -> List[Dict[str, str]]:
    """Prompt for the first pass (project selection)."""
    # Convert resume_tex to string if it's a list
    if isinstance(resume_tex, list):
        resume_tex = "\n".join(resume_tex)
    
    res_to_send = _budgeted_resume(resume_tex, jd_text, role, company)
    
    # Generate enhanced context if projects are provided
    enhanced_context = ""
    if projects:
        context_data = enhance_project_selection_prompt(role, company, jd_text, projects)
        enhanced_context = f"""
ENHANCED GUIDELINES:
{context_data['enhanced_instructions']}

ROLE KEYWORDS: {', '.join(context_data['role_keywords'])}

PROJECT KEYWORD SUMMARY:
{_format_project_summaries(context_data['project_summaries'])}
"""
    
    user = f"""ROLE: {role}
COMPANY: {company}

JOB DESCRIPTION:
\"\"\"{jd_text}\"\"\"
{enhanced_context}
FULL LATEX RESUME:
\"\"\"{res_to_send}\"\"\"
"""
    return [
        {"role": "system", "content": SYSTEM_P1},
        {"role": "user",   "content": user},
    ]

# ---------- PASS‑2 prompt: bullet + skills rewrites ----------------------- #
SYSTEM_P2 = """\
You are a résumé‑tailor assistant specializing in optimizing resume content for maximum impact and relevance.

Return ONLY valid JSON:
{
  "bullets": [ { "old": "<exact old bullet>", "new": "<rewritten bullet>" } ],
  "skills_block": "<complete replacement line for the Technical Skills block>"
}

Rules:
• Each rewritten bullet ≤ 32 words; keep metrics (%, ms, ×) intact.
• Insert each missing keyword from the JD at most once; no stuffing.
• skills_block must preserve LaTeX syntax (it starts with \\textbf{Languages:} … } ).
• Do NOT invent experience not already present.
• Focus on ACHIEVEMENTS and IMPACT, not just responsibilities.
• Use strong action verbs at the beginning of each bullet.
• Quantify achievements with metrics where possible.
"""

def build_messages_pass2(
        jd_text: str,
        role: str,
        company: str,
        updated_resume_tex: list[str] or str,
) -> List[Dict[str, str]]:
    """Prompt for the second pass (rewrite bullets & skills)."""
    # Convert updated_resume_tex to string if it's a list
    if isinstance(updated_resume_tex, list):
        updated_resume_tex = "\n".join(updated_resume_tex)
        
    res_to_send = _budgeted_resume(updated_resume_tex, jd_text, role, company)
    
    # Get enhanced context for bullet rewrites
    context_data = enhance_bullet_rewrite_prompt(role, company, jd_text, updated_resume_tex)
    
    # Get role-specific examples
    examples = create_examples_for_bullets(role)
    examples_text = _format_examples(examples)
    
    enhanced_context = f"""
ENHANCED GUIDELINES:
{context_data['enhanced_instructions']}

SKILLS SECTION GUIDANCE:
{context_data['skills_instructions']}

JOB KEYWORDS: {', '.join(context_data['job_requirements'])}

BULLET POINT REWRITE EXAMPLES:
{examples_text}
"""
    
    user = f"""ROLE: {role}
COMPANY: {company}

JOB DESCRIPTION:
\"\"\"{jd_text}\"\"\"
{enhanced_context}
UPDATED RESUME (projects already set):
\"\"\"{res_to_send}\"\"\"
"""
    return [
        {"role": "system", "content": SYSTEM_P2},
        {"role": "user",   "content": user},
    ]

# ---------- shared helper to respect token budget ------------------------ #
def _budgeted_resume(resume_tex: str, jd_text: str, role: str, company: str) -> str:
    """Return either the full or compressed resume depending on token headroom."""
    tok_resume  = approx_tokens(resume_tex)
    tok_jd      = approx_tokens(jd_text)
    tok_other   = approx_tokens(role + company) + 500  # padding for JSON reply

    if tok_resume + tok_jd + tok_other > SAFETY_MARGIN:
        resume_tex = compress_resume(resume_tex)
    return resume_tex

# ---------- formatting helpers for enhanced content ---------------------- #
def _format_project_summaries(summaries: List[Dict]) -> str:
    """Format project summaries for the prompt."""
    formatted = []
    for project in summaries:
        formatted.append(f"• {project['title']}: {', '.join(project['keywords'])}")
    return "\n".join(formatted)

def _format_examples(examples: List[Dict[str, str]]) -> str:
    """Format bullet point rewrite examples for the prompt."""
    formatted = []
    for i, example in enumerate(examples, 1):
        formatted.append(f"Example {i}:")
        formatted.append(f"  BEFORE: {example['original']}")
        formatted.append(f"  AFTER:  {example['improved']}")
        formatted.append("")
    return "\n".join(formatted)
