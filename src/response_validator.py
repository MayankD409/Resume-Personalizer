"""
This module provides validation for LLM responses to ensure they match expected schemas
and handle gracefully when they don't.
"""
from typing import Dict, Any, Optional
import logging
import json

logger = logging.getLogger(__name__)

# Define expected schema structures
PROJECT_SELECTION_SCHEMA = {
    "required_fields": ["include_projects", "exclude_projects"],
    "field_types": {
        "include_projects": list,
        "exclude_projects": list
    }
}

REWRITE_SCHEMA = {
    "required_fields": ["bullets", "skills_block"],
    "field_types": {
        "bullets": list,
        "skills_block": str
    },
    "nested_fields": {
        "bullets": {
            "item_fields": ["old", "new"],
            "item_types": {"old": str, "new": str}
        }
    }
}

def validate_response(response: Dict[str, Any], schema_type: str = "project_selection") -> Optional[Dict[str, Any]]:
    """
    Validates the LLM response against the expected schema.
    
    Args:
        response: The response dictionary from the LLM
        schema_type: Type of schema to validate against ("project_selection" or "rewrite")
        
    Returns:
        Validated and cleaned response dict or None if validation fails
    """
    schema = PROJECT_SELECTION_SCHEMA if schema_type == "project_selection" else REWRITE_SCHEMA
    
    # Check if all required fields exist
    for field in schema["required_fields"]:
        if field not in response:
            logger.error(f"Missing required field '{field}' in {schema_type} response")
            return None
            
    # Check field types
    for field, expected_type in schema["field_types"].items():
        if field in response and not isinstance(response[field], expected_type):
            # Try to convert if possible
            try:
                if expected_type is list and isinstance(response[field], str):
                    # Handle case where list might be returned as string
                    response[field] = json.loads(response[field])
                else:
                    response[field] = expected_type(response[field])
                logger.warning(f"Converted field '{field}' to {expected_type.__name__}")
            except (ValueError, TypeError, json.JSONDecodeError):
                logger.error(f"Field '{field}' has incorrect type. Expected {expected_type.__name__}")
                return None
    
    # Check nested fields (for bullets in rewrite schema)
    if schema_type == "rewrite" and "bullets" in response:
        valid_bullets = []
        for i, bullet in enumerate(response["bullets"]):
            if not isinstance(bullet, dict):
                logger.warning(f"Bullet at index {i} is not a dictionary, skipping")
                continue
                
            # Check for required fields in each bullet
            if not all(field in bullet for field in schema["nested_fields"]["bullets"]["item_fields"]):
                logger.warning(f"Bullet at index {i} missing required fields, skipping")
                continue
                
            # Check field types in bullets
            valid_bullet = True
            for field, expected_type in schema["nested_fields"]["bullets"]["item_types"].items():
                if field in bullet and not isinstance(bullet[field], expected_type):
                    logger.warning(f"Bullet field '{field}' at index {i} has wrong type, skipping")
                    valid_bullet = False
                    break
                    
            if valid_bullet:
                valid_bullets.append(bullet)
        
        response["bullets"] = valid_bullets
        
    # Sanitize skills block - ensure it starts with \textbf{Languages:
    if schema_type == "rewrite" and "skills_block" in response:
        skills = response["skills_block"]
        if not skills.strip().startswith("\\textbf{Languages:"):
            logger.warning("Skills block doesn't start with expected format, attempting repair")
            if "Languages:" in skills:
                skills = skills.replace("Languages:", "\\textbf{Languages:")
                if not "}" in skills:
                    # Add closing brace if missing
                    parts = skills.split(",", 1)
                    if len(parts) > 1:
                        skills = f"{parts[0]}}} {parts[1]}"
                response["skills_block"] = skills
                
    return response

def format_validation_error(schema_type: str) -> str:
    """
    Returns a user-friendly error message for validation failures.
    
    Args:
        schema_type: Type of schema that failed validation
        
    Returns:
        Formatted error message with expected format
    """
    if schema_type == "project_selection":
        return (
            "The AI response for project selection was invalid. Expected format:\n"
            "{\n"
            '  "include_projects": ["Project Title 1", "Project Title 2"],\n'
            '  "exclude_projects": ["Project Title 3"]\n'
            "}"
        )
    else:  # rewrite
        return (
            "The AI response for rewriting was invalid. Expected format:\n"
            "{\n"
            '  "bullets": [\n'
            '    {"old": "Original bullet text", "new": "Rewritten bullet text"},\n'
            '    {"old": "Another bullet", "new": "Improved bullet"}\n'
            "  ],\n"
            '  "skills_block": "\\\\textbf{Languages:} Python, JavaScript, ..."\n'
            "}"
        ) 