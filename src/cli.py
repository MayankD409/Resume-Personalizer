# Parse command line arguments
import argparse
from rich import print
from rich.console import Console
from src.io_utils import load_jd_text, load_template
from src.path_utils import prepare_output_dir
from src.latex_parser import extract_project_blocks, toggle_block
from src.prompt_builder import build_messages_pass1, build_messages_pass2
from src.project_chooser import decide_projects
from src.rewrite_applier import apply_bullet_rewrites, replace_skills_block
from src.response_validator import validate_response, format_validation_error
from src.keyword_analyzer import analyze_keyword_match, get_keyword_recommendations, format_keyword_report
from src.interactive_mode import interactive_modifications
from src.ai_client import AIClient
import pathlib
import logging
import sys
import os

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

console = Console()

def build_parser():
    p = argparse.ArgumentParser(prog="resume-tailor", description="Automate LaTeX resume tailoring for a Job Description.")
    p.add_argument("--jd-file", help="Path to JD .txt/.pdf/.docx")
    p.add_argument("--jd-text", help="Paste JD string directly (mutually exclusive)")
    p.add_argument("--role", help="Job role being applied for", required=True)
    p.add_argument("--company", help="Company name", required=True)
    p.add_argument("--template", help="Path to template .tex file", default="templates/resume_template.tex")
    p.add_argument("--mode", help="Output mode ('interactive', 'auto', 'preview')", default="interactive")
    p.add_argument("--output", help="Output path for the tailored resume", default="output")
    p.add_argument("--debug", help="Enable debug logging", action="store_true")
    p.add_argument("--model", help="AI model to use", default="gpt-4o")
    p.add_argument("--keyword-analysis", help="Enable keyword matching analysis", action="store_true")
    p.add_argument("--no-color", help="Disable colored output", action="store_true")
    return p

def run_tailor_workflow(args):
    # Process arguments
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        
    # Configure color support
    os.environ["COLORTERM"] = "off" if args.no_color else "truecolor"
        
    # Load JD text
    if args.jd_file:
        jd_text = load_jd_text(args.jd_file)
    elif args.jd_text:
        jd_text = args.jd_text
    else:
        console.print("[bold red]Error:[/bold red] Either --jd-file or --jd-text must be provided")
        return 1
    
    # Initialize AI client with model preference
    ai = AIClient(model=args.model)
    
    # Create output directory
    output_dir = prepare_output_dir(args.output, args.company, args.role)
    
    # Load template
    tpl_path = pathlib.Path(args.template)
    resume_text = load_template(tpl_path)
    
    # Parse resume lines for project blocks
    lines = resume_text  # resume_text is already a list of lines
    console.print(f"[bold cyan]Phase 1:[/bold cyan] Analyzing resume and project blocks...")
    blocks = extract_project_blocks(lines)
    
    if not blocks:
        console.print("[bold red]Error:[/bold red] No project blocks found in the resume. Check LaTeX format.")
        return 1
    
    console.print(f"Found [bold]{len(blocks)}[/bold] project blocks in resume.")
    
    # FIRST LLM CALL - Project Selection
    console.print(f"\n[bold cyan]Phase 2:[/bold cyan] Selecting projects for {args.role} at {args.company}...")
    
    messages1 = build_messages_pass1(jd_text, args.role, args.company, resume_text, blocks)
    response1 = ai.ask(messages1)
    
    # Validate the response
    validated_response1 = validate_response(response1, "project_selection")
    if not validated_response1:
        console.print(f"[bold red]Error:[/bold red] Invalid response from AI model")
        console.print(format_validation_error("project_selection"))
        return 1
        
    # Use project chooser to determine blocks to activate/deactivate
    blocks_to_activate, blocks_to_deactivate = decide_projects(validated_response1, blocks)
    
    # Apply toggles
    for block in blocks_to_activate:
        toggle_block(lines, block, activate=True)
        console.print(f"[green]Activated:[/green] {block.get('title', 'Unnamed project')}")
        
    for block in blocks_to_deactivate:
        toggle_block(lines, block, activate=False)
        console.print(f"[yellow]Deactivated:[/yellow] {block.get('title', 'Unnamed project')}")
        
    # Create updated resume text
    updated_resume = "\n".join(lines)
    
    # Run keyword analysis on updated resume if enabled
    keyword_metrics = None
    if args.keyword_analysis:
        console.print(f"\n[bold cyan]Analyzing Keyword Match:[/bold cyan]")
        keyword_metrics = analyze_keyword_match(jd_text, updated_resume)
        console.print(format_keyword_report(keyword_metrics, colorize=not args.no_color))
        recommended_keywords = get_keyword_recommendations(jd_text, updated_resume)
        if recommended_keywords:
            console.print("\n[bold]Recommended Keywords to Include:[/bold]")
            console.print(", ".join(recommended_keywords))
    
    # SECOND LLM CALL - Bullet Rewriting
    console.print(f"\n[bold cyan]Phase 3:[/bold cyan] Rewriting bullet points and skills for impact...")
    
    messages2 = build_messages_pass2(jd_text, args.role, args.company, updated_resume)
    response2 = ai.ask(messages2)
    
    # Validate the response
    validated_response2 = validate_response(response2, "rewrite")
    if not validated_response2:
        console.print(f"[bold red]Error:[/bold red] Invalid response from AI model")
        console.print(format_validation_error("rewrite"))
        return 1
    
    # Get bullets and skills section from response
    bullets = validated_response2.get("bullets", [])
    skills_block = validated_response2.get("skills_block", "")
    
    # Make a copy of lines for modification
    modified_lines = lines.copy()
    
    # Apply automatic changes to the copy
    applied_count = apply_bullet_rewrites(modified_lines, bullets)
    skills_updated = replace_skills_block(modified_lines, skills_block)
    
    console.print(f"Rewrote [bold]{applied_count}[/bold] bullet points")
    if skills_updated:
        console.print(f"Updated technical skills section")
        
    # Handle different modes
    if args.mode == "interactive":
        # Interactive mode with user review
        console.print(f"\n[bold cyan]Phase 4:[/bold cyan] Interactive review and selection...")
        final_lines = interactive_modifications(
            lines,
            modified_lines,
            bullets,
            skills_block,
            keyword_metrics
        )
    elif args.mode == "preview":
        # Preview mode - just show changes without saving
        from src.interactive_mode import show_diff_lines, preview_changes
        console.print("\n[bold]Changes Preview:[/bold]")
        show_diff_lines(lines, modified_lines)
        preview_changes(lines, bullets)
        console.print("\n[italic]Preview mode - no changes saved[/italic]")
        return 0
    else:
        # Auto mode - apply all changes
        final_lines = modified_lines
    
    # Save the final result
    output_path = os.path.join(output_dir, "tailored_resume.tex")
    with open(output_path, 'w') as f:
        f.write("\n".join(final_lines))
    
    console.print(f"\n[bold green]Success![/bold green] Tailored resume saved to: {output_path}")
    
    # Compile PDF if possible (TO BE IMPLEMENTED IN PHASE 3)
    return 0

def main():
    parser = build_parser()
    args = parser.parse_args()
    
    try:
        return run_tailor_workflow(args)
    except Exception as e:
        logger.exception(f"Error running resume-tailor: {e}")
        console.print(f"[bold red]Error:[/bold red] {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
 