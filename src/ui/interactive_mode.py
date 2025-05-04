"""
This module provides interactive editing features for the resume-tailor tool,
including diff previews and selective application of changes.
"""
from typing import List, Dict, Optional, Tuple, Any
import difflib
from rich import print as rprint
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table
import os
import re

console = Console()

def colorize_diff(old_line: str, new_line: str) -> Tuple[str, str]:
    """
    Create color-highlighted versions of old and new lines to show differences.
    
    Args:
        old_line: Original line
        new_line: Modified line
        
    Returns:
        Tuple of (colorized old line, colorized new line)
    """
    old_words = old_line.split()
    new_words = new_line.split()
    
    # Create a sequence matcher
    matcher = difflib.SequenceMatcher(None, old_words, new_words)
    
    # Colorize old line (deletions)
    old_colorized = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            old_colorized.extend(old_words[i1:i2])
        elif tag in ('replace', 'delete'):
            old_colorized.extend([f"[red]{word}[/red]" for word in old_words[i1:i2]])
    
    # Colorize new line (additions)
    new_colorized = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            new_colorized.extend(new_words[j1:j2])
        elif tag in ('replace', 'insert'):
            new_colorized.extend([f"[green]{word}[/green]" for word in new_words[j1:j2]])
    
    return ' '.join(old_colorized), ' '.join(new_colorized)

def show_diff_lines(orig_lines: List[str], modified_lines: List[str], context_lines: int = 3) -> None:
    """
    Show a unified diff of changes with context lines.
    
    Args:
        orig_lines: Original lines
        modified_lines: Modified lines
        context_lines: Number of context lines to show around changes
    """
    diff = list(difflib.unified_diff(
        orig_lines, 
        modified_lines,
        lineterm='',
        n=context_lines
    ))
    
    if diff:
        syntax = Syntax('\n'.join(diff), "diff", theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title="Changes to be Applied", expand=False))
    else:
        console.print("[yellow]No changes detected[/yellow]")

def preview_changes(orig_lines: List[str], bullet_rewrites: List[Dict[str, str]]) -> None:
    """
    Show a preview of bullet point changes.
    
    Args:
        orig_lines: Original resume lines
        bullet_rewrites: List of bullet point rewrites
    """
    if not bullet_rewrites:
        console.print("[yellow]No bullet point changes to preview[/yellow]")
        return
        
    table = Table(title="Bullet Point Changes")
    table.add_column("Original", style="red")
    table.add_column("Rewritten", style="green")
    
    for rewrite in bullet_rewrites:
        old = rewrite.get('old', '').strip()
        new = rewrite.get('new', '').strip()
        if old and new:
            table.add_row(old, new)
            
    console.print(table)

def review_and_select_changes(
    bullet_rewrites: List[Dict[str, str]],
    skills_replacement: str,
    keyword_recommendations: Optional[List[str]] = None
) -> Tuple[List[Dict[str, str]], bool]:
    """
    Show and allow user to select which changes to apply.
    
    Args:
        bullet_rewrites: List of bullet point rewrites
        skills_replacement: Skills section replacement
        keyword_recommendations: Optional list of recommended keywords
        
    Returns:
        Tuple of (selected bullet rewrites, apply_skills_flag)
    """
    selected_bullets = []
    apply_skills = False
    
    # Show keyword recommendations if available
    if keyword_recommendations:
        console.print("\n[bold cyan]Keyword Recommendations:[/bold cyan]")
        console.print("Consider including these keywords in your resume:")
        for i, keyword in enumerate(keyword_recommendations[:10], 1):
            console.print(f"{i}. [yellow]{keyword}[/yellow]")
        console.print()
    
    # Show bullet point changes
    if bullet_rewrites:
        console.print("\n[bold cyan]Bullet Point Rewrites:[/bold cyan]")
        for i, rewrite in enumerate(bullet_rewrites, 1):
            old = rewrite.get('old', '').strip()
            new = rewrite.get('new', '').strip()
            
            if old and new:
                old_colored, new_colored = colorize_diff(old, new)
                
                console.print(f"[bold]{i}. Original:[/bold]")
                console.print(f"   {old_colored}")
                console.print(f"[bold]   Rewritten:[/bold]")
                console.print(f"   {new_colored}")
                console.print()
                
                if Confirm.ask(f"Apply this change?", default=True):
                    selected_bullets.append(rewrite)
                    
    # Show skills replacement
    if skills_replacement:
        console.print("\n[bold cyan]Technical Skills Replacement:[/bold cyan]")
        console.print(f"[green]{skills_replacement}[/green]")
        apply_skills = Confirm.ask("Apply this skills replacement?", default=True)
    
    return selected_bullets, apply_skills

def show_match_metrics(metrics: Dict[str, Any]) -> None:
    """
    Display job description match metrics.
    
    Args:
        metrics: Dictionary of matching metrics
    """
    match_percentage = metrics.get("match_percentage", 0)
    
    # Determine match level and color
    if match_percentage >= 80:
        color = "green"
        match_level = "Excellent"
    elif match_percentage >= 60:
        color = "yellow"
        match_level = "Good"
    else:
        color = "red"
        match_level = "Needs Improvement"
    
    # Create a panel for the metrics
    console.print()
    console.print(Panel(
        f"[bold]{match_level} Match: [/{color}]{match_percentage:.1f}%[/]\n\n"
        f"[bold]Matched Keywords:[/] {', '.join(metrics.get('matched_keywords', [])[:7])}\n"
        f"[bold]Missing Keywords:[/] {', '.join(metrics.get('missing_keywords', [])[:7])}",
        title="Job Match Analysis",
        border_style=color
    ))

def interactive_modifications(
    original_lines: List[str],
    modified_lines: List[str],
    bullet_rewrites: List[Dict[str, str]],
    skills_block: str,
    keyword_metrics: Optional[Dict] = None
) -> List[str]:
    """
    Interactive session to review and apply resume modifications.
    
    Args:
        original_lines: Original resume lines
        modified_lines: Modified resume after automatic changes
        bullet_rewrites: List of bullet point rewrites
        skills_block: New skills block content
        keyword_metrics: Optional keyword matching metrics
        
    Returns:
        Final modified resume lines after user review
    """
    console.print("\n[bold cyan]Resume Tailoring Interactive Session[/bold cyan]")
    
    # Show match metrics if available
    if keyword_metrics:
        show_match_metrics(keyword_metrics)
    
    # Show diff
    console.print("\n[bold]Overall Changes Preview:[/bold]")
    show_diff_lines(original_lines, modified_lines)
    
    # Ask for detailed review
    if Confirm.ask("\nWould you like to review changes in detail?", default=True):
        # Get recommended keywords
        keyword_recommendations = keyword_metrics.get("missing_keywords", []) if keyword_metrics else None
        
        # Show detailed changes and get user selections
        selected_bullets, apply_skills = review_and_select_changes(
            bullet_rewrites, 
            skills_block,
            keyword_recommendations
        )
        
        # Apply only selected changes
        final_lines = original_lines.copy()
        
        # Apply selected bullet changes
        from src.rewrite_applier import apply_bullet_rewrites
        if selected_bullets:
            apply_bullet_rewrites(final_lines, selected_bullets)
        
        # Apply skills block if selected
        if apply_skills and skills_block:
            from src.rewrite_applier import replace_skills_block
            replace_skills_block(final_lines, skills_block)
            
        return final_lines
    else:
        # Apply all changes
        return modified_lines

def input_with_prefill(prompt: str, prefill: str = '') -> str:
    """
    Get user input with prefilled value that can be edited.
    
    Args:
        prompt: Prompt text
        prefill: Prefilled text
        
    Returns:
        User input text
    """
    # Attempt to use readline for prefill functionality
    try:
        import readline
        readline.set_startup_hook(lambda: readline.insert_text(prefill))
        try:
            return input(prompt)
        finally:
            readline.set_startup_hook()
    except (ImportError, AttributeError):
        # Fallback if readline not available
        console.print(f"{prompt} [dim](Current: {prefill})[/dim]")
        return input("New value (leave empty to keep current): ") or prefill 