"""
This module handles the selection of projects to include/exclude in the resume
based on the AI's response.
"""
from typing import List, Dict, Tuple, Optional
import difflib
import re
import logging

logger = logging.getLogger(__name__)

def decide_projects(ai_json: Dict, blocks: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """
    Takes the AI model's JSON response and the extracted LaTeX project blocks,
    and determines which blocks to activate and deactivate.
    
    Args:
        ai_json: Dictionary containing 'include_projects' and 'exclude_projects' lists
        blocks: List of project block dictionaries from latex_parser.extract_project_blocks()
    
    Returns:
        Tuple of (blocks_to_activate, blocks_to_deactivate)
    """
    # Extract project lists from AI response
    include_projects = ai_json.get('include_projects', [])
    exclude_projects = ai_json.get('exclude_projects', [])
    
    # Log the AI's decision
    logger.info(f"AI recommends including: {', '.join(include_projects)}")
    logger.info(f"AI recommends excluding: {', '.join(exclude_projects)}")
    
    blocks_to_activate = []
    blocks_to_deactivate = []
    
    # Extract existing block titles for fuzzy matching
    block_titles = {block['title']: block for block in blocks}
    
    # First pass: handle exact matches
    matched_includes = set()
    matched_excludes = set()
    
    for block in blocks:
        title = block['title']
        
        # Handle blocks to activate (exact match)
        if title in include_projects:
            if not block['active']:  # Only include if it's not already active
                blocks_to_activate.append(block)
            matched_includes.add(title)
        
        # Handle blocks to deactivate (exact match)
        elif title in exclude_projects:
            if block['active']:  # Only include if it's currently active
                blocks_to_deactivate.append(block)
            matched_excludes.add(title)
    
    # Second pass: handle fuzzy matches for unmatched projects
    unmatched_includes = [p for p in include_projects if p not in matched_includes]
    unmatched_excludes = [p for p in exclude_projects if p not in matched_excludes]
    
    if unmatched_includes or unmatched_excludes:
        logger.info("Using fuzzy matching for unmatched project titles")
        
        # Process fuzzy matches for includes
        for include_title in unmatched_includes:
            matched_block = find_best_matching_block(include_title, blocks, threshold=0.75)
            if matched_block and not matched_block['active']:
                blocks_to_activate.append(matched_block)
                logger.info(f"Fuzzy matched include: '{include_title}' -> '{matched_block['title']}'")
        
        # Process fuzzy matches for excludes
        for exclude_title in unmatched_excludes:
            matched_block = find_best_matching_block(exclude_title, blocks, threshold=0.75)
            if matched_block and matched_block['active']:
                blocks_to_deactivate.append(matched_block)
                logger.info(f"Fuzzy matched exclude: '{exclude_title}' -> '{matched_block['title']}'")
    
    # Handle special case: all projects are inactive, but we need to show some
    if not blocks_to_activate and all(not block['active'] for block in blocks):
        logger.warning("All projects are currently inactive, activating top recommendations")
        
        # Sort blocks based on their priority in the include list
        priority_blocks = []
        for title in include_projects:
            matched_block = find_best_matching_block(title, blocks, threshold=0.65)
            if matched_block:
                priority_blocks.append(matched_block)
        
        # If we still don't have any blocks to activate, take the first few blocks
        if not priority_blocks and blocks:
            logger.warning("No matches found in include list, using the first few blocks")
            priority_blocks = blocks[:min(3, len(blocks))]
        
        # Add the priority blocks to blocks_to_activate
        for block in priority_blocks:
            if block not in blocks_to_activate:
                blocks_to_activate.append(block)
    
    # Ensure we don't activate the same block that we're deactivating
    blocks_to_activate = [b for b in blocks_to_activate if b not in blocks_to_deactivate]
    
    return blocks_to_activate, blocks_to_deactivate

def find_best_matching_block(title: str, blocks: List[Dict], threshold: float = 0.7) -> Optional[Dict]:
    """
    Find the block with the best fuzzy match to the given title.
    
    Args:
        title: The project title to match
        blocks: List of project blocks
        threshold: Minimum similarity score to consider a match
        
    Returns:
        The best matching block, or None if no good match is found
    """
    best_score = 0
    best_block = None
    
    # Clean the title for matching
    clean_title = _clean_string_for_matching(title)
    
    for block in blocks:
        block_title = _clean_string_for_matching(block['title'])
        
        # Try to match with different metrics
        # 1. Direct string similarity
        similarity = difflib.SequenceMatcher(None, clean_title, block_title).ratio()
        
        # 2. Keyword matching (check if all the important words are present)
        keywords = set(re.findall(r'\b\w+\b', clean_title.lower()))
        if keywords:
            block_keywords = set(re.findall(r'\b\w+\b', block_title.lower()))
            keyword_coverage = len(keywords.intersection(block_keywords)) / len(keywords)
            # Boost score if keywords are present
            similarity = max(similarity, keyword_coverage * 0.9)
        
        # 3. Title inclusion (one contains the other)
        if clean_title in block_title or block_title in clean_title:
            similarity = max(similarity, 0.85)
        
        if similarity > best_score:
            best_score = similarity
            best_block = block
    
    # Only return if we have a good match
    if best_score >= threshold:
        return best_block
    
    return None

def _clean_string_for_matching(text: str) -> str:
    """
    Clean a string for fuzzy matching by removing extra spaces,
    lowercasing, and removing common filler words.
    
    Args:
        text: The string to clean
        
    Returns:
        Cleaned string
    """
    # Remove LaTeX commands
    text = re.sub(r'\\[a-zA-Z]+\{|\}', '', text)
    
    # Lowercase and remove extra spaces
    text = ' '.join(text.lower().split())
    
    # Remove common filler words
    filler_words = {'the', 'a', 'an', 'and', 'or', 'of', 'for', 'in', 'on', 'at', 'to'}
    words = text.split()
    filtered_words = [w for w in words if w not in filler_words]
    
    return ' '.join(filtered_words) 