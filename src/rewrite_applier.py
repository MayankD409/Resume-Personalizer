"""
This module handles applying bullet point rewrites and replacing the skills block
in the LaTeX resume based on the AI's recommendations.
"""
from typing import List, Dict, Optional, Tuple
import re
import difflib

def apply_bullet_rewrites(lines: List[str], bullet_json_list: List[Dict]) -> int:
    """
    For each {old, new} pair in the bullet_json_list, find the exact LaTeX line 
    containing the old bullet and replace it with the new bullet.
    
    Args:
        lines: List of lines from the LaTeX resume
        bullet_json_list: List of dictionaries with 'old' and 'new' keys
    
    Returns:
        Number of successfully applied bullet rewrites
    """
    applied_count = 0
    
    # Process each bullet rewrite
    for bullet_pair in bullet_json_list:
        old_bullet = bullet_pair.get('old', '').strip()
        new_bullet = bullet_pair.get('new', '').strip()
        
        if not old_bullet or not new_bullet:
            continue
        
        # Find the best matching line for the old bullet
        best_match = find_best_match(lines, old_bullet)
        if best_match:
            line_index, match_score, original_line = best_match
            
            # Only apply if we have a good match (similarity > 0.8)
            if match_score >= 0.8:
                # Replace while preserving leading whitespace and LaTeX commands
                lines[line_index] = apply_replacement(original_line, old_bullet, new_bullet)
                applied_count += 1
    
    return applied_count

def find_best_match(lines: List[str], target_text: str) -> Optional[Tuple[int, float, str]]:
    """
    Find the line that best matches the target text using fuzzy matching.
    
    Args:
        lines: List of lines to search through
        target_text: The text to find
        
    Returns:
        Tuple of (line index, match score, original line) or None if no good match
    """
    best_score = 0.0
    best_line_index = -1
    best_line = ""
    
    # Clean target for comparison
    clean_target = ' '.join(target_text.split())
    
    for i, line in enumerate(lines):
        # Clean line for comparison
        clean_line = ' '.join(line.strip().split())
        
        # Skip very short lines or empty lines
        if len(clean_line) < 10:
            continue
            
        # Use difflib to calculate similarity ratio
        similarity = difflib.SequenceMatcher(None, clean_line, clean_target).ratio()
        
        # Check for exact substring match which gets high priority
        if clean_target in clean_line:
            # Adjust score based on how much of the line matches the target
            relative_length = len(clean_target) / len(clean_line)
            # Score higher when the target takes up more of the line
            similarity = max(similarity, 0.7 + 0.3 * relative_length)
            
        if similarity > best_score:
            best_score = similarity
            best_line_index = i
            best_line = line
            
            # Early exit if we find a perfect or near-perfect match
            if similarity > 0.95:
                break
                
    if best_score > 0:
        return best_line_index, best_score, best_line
    return None

def apply_replacement(original_line: str, old_text: str, new_text: str) -> str:
    """
    Apply a replacement while preserving leading whitespace and LaTeX commands.
    
    Args:
        original_line: The original line from the file
        old_text: The text to replace
        new_text: The replacement text
        
    Returns:
        Updated line
    """
    # Preserve leading whitespace
    leading_space = re.match(r'^\s*', original_line).group(0)
    
    # Check if the line starts with LaTeX command and preserve it
    latex_prefix = ""
    latex_match = re.match(r'^\s*(\\[a-zA-Z]+(?:\[[^\]]*\])?(?:\{[^}]*\})?\s*)', original_line)
    if latex_match:
        latex_prefix = latex_match.group(1)
    
    # Create the new line
    clean_line = original_line.strip()
    
    # Replace while preserving LaTeX context
    if old_text in clean_line:
        # Simple case: direct replacement
        replaced_line = clean_line.replace(old_text, new_text)
    else:
        # Fuzzy replacement - replace most of the text after LaTeX commands
        clean_old_text = ' '.join(old_text.split())
        clean_new_text = ' '.join(new_text.split())
        
        # Try to find similar text patterns and make intelligent replacement
        words_old = clean_old_text.split()
        words_line = clean_line.split()
        
        # Find the starting word match position
        start_pos = -1
        for i in range(len(words_line) - min(3, len(words_old)) + 1):
            window = ' '.join(words_line[i:i+min(5, len(words_old))])
            if difflib.SequenceMatcher(None, window, clean_old_text[:min(len(window), len(clean_old_text))]).ratio() > 0.6:
                start_pos = i
                break
                
        if start_pos >= 0:
            # Replace from the start position to the end or a reasonable stopping point
            end_pos = min(start_pos + len(words_old) + 3, len(words_line))
            replaced_line = ' '.join(words_line[:start_pos] + clean_new_text.split() + words_line[end_pos:])
        else:
            # Fallback if we can't find a good place to start
            replaced_line = latex_prefix + clean_new_text if latex_prefix else clean_new_text
    
    # Return with original leading whitespace
    return leading_space + replaced_line

def replace_skills_block(lines: List[str], new_line: str) -> bool:
    """
    Locate the existing Technical Skills line (starts with \textbf{Languages:})
    and replace it entirely with new_line.
    
    Args:
        lines: List of lines from the LaTeX resume
        new_line: Complete replacement line for the skills section
    
    Returns:
        True if successfully replaced, False otherwise
    """
    # Improved pattern to handle variations
    skills_patterns = [
        re.compile(r'\\textbf\{Languages:'),
        re.compile(r'\\textbf\{Skills:'),
        re.compile(r'\\textbf\{Technical Skills:'),
        re.compile(r'Languages:', re.IGNORECASE),
        re.compile(r'Technical Skills:', re.IGNORECASE)
    ]
    
    for i, line in enumerate(lines):
        for pattern in skills_patterns:
            if pattern.search(line):
                # Preserve leading whitespace
                leading_space = re.match(r'^\s*', line).group(0)
                lines[i] = leading_space + new_line.strip()
                return True
    
    return False 