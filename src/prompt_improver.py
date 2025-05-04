"""
This module provides enhancements for the prompt templates to provide better 
context awareness and improve the quality of AI-generated resume tailoring.
"""
from typing import Dict, List, Optional, Any
import re
from src.keyword_analyzer import extract_keywords

def enhance_project_selection_prompt(
    role: str, 
    company: str, 
    jd_text: str, 
    projects: List[Dict]
) -> Dict[str, Any]:
    """
    Enhance the project selection prompt with additional context and instructions.
    
    Args:
        role: Job role title
        company: Company name
        jd_text: Job description text
        projects: List of project blocks extracted from the resume
        
    Returns:
        Dictionary with enhanced context and instructions
    """
    # Extract key requirements from JD
    jd_keywords = extract_keywords(jd_text, top_n=15)
    
    # Extract project types and tech stacks
    project_summaries = []
    for i, project in enumerate(projects):
        # Get project title
        title_match = re.search(r'\\textbf\{(.*?)\}', project.get('content', ''))
        title = title_match.group(1) if title_match else f"Project {i+1}"
        
        # Extract tech stack and key skills from project
        project_content = project.get('content', '')
        keywords = extract_keywords(project_content, top_n=8)
        
        project_summaries.append({
            "title": title,
            "keywords": keywords
        })
    
    # Create specific instructions for project selection
    enhanced_context = {
        "role_keywords": jd_keywords,
        "project_summaries": project_summaries,
        "enhanced_instructions": (
            f"As a professional resume tailoring expert, your task is to select the most relevant "
            f"projects from the candidate's resume for a {role} position at {company}.\n\n"
            f"IMPORTANT SELECTION CRITERIA:\n"
            f"1. Prioritize projects that demonstrate skills mentioned in the job description\n"
            f"2. Include projects with technologies/tools relevant to {role} roles\n"
            f"3. Prefer recent and impactful projects over older ones\n"
            f"4. Select diverse projects that showcase different skills when appropriate\n"
            f"5. Consider the company culture and values of {company} in your selection\n\n"
            f"For each project, carefully evaluate how well it aligns with the job requirements "
            f"and how effectively it demonstrates the candidate's qualifications for this specific role."
        )
    }
    
    return enhanced_context

def enhance_bullet_rewrite_prompt(
    role: str, 
    company: str, 
    jd_text: str, 
    resume_text: str
) -> Dict[str, Any]:
    """
    Enhance the bullet rewrite prompt with additional context and instructions.
    
    Args:
        role: Job role title
        company: Company name
        jd_text: Job description text
        resume_text: Current resume text after project selection
        
    Returns:
        Dictionary with enhanced context and instructions
    """
    # Extract key requirements and skills from JD
    jd_keywords = extract_keywords(jd_text, top_n=20)
    
    # Create specific instructions for bullet rewriting
    enhanced_context = {
        "job_requirements": jd_keywords,
        "enhanced_instructions": (
            f"As an expert resume writer specializing in {role} positions, your task is to rewrite "
            f"the bullet points to better align with this specific {role} role at {company}.\n\n"
            f"BULLET POINT REWRITING GUIDELINES:\n"
            f"1. Focus each bullet on ACHIEVEMENTS and IMPACT, not just responsibilities\n"
            f"2. Use strong action verbs at the beginning of each bullet\n"
            f"3. Quantify achievements with specific metrics where possible (%, $, time saved, etc.)\n"
            f"4. Incorporate relevant keywords from the job description naturally\n"
            f"5. Keep each bullet concise (1-2 lines) and focused on a single accomplishment\n"
            f"6. Emphasize skills and experiences most relevant to a {role} position\n"
            f"7. Maintain the candidate's existing technical terminology for authenticity\n"
            f"8. For technical projects, highlight both technical skills and business outcomes\n\n"
            f"IMPORTANT: Preserve the core facts of each bullet while optimizing the wording, "
            f"and maintain proper LaTeX formatting."
        ),
        "skills_instructions": (
            f"For the Technical Skills section, reorganize the languages and technologies "
            f"based on relevance to this {role} position. Place the most relevant skills first "
            f"and ensure the format matches: \\textbf{{Languages:}} Skill1, Skill2, ...; "
            f"\\textbf{{Frameworks:}} Framework1, Framework2, ...; etc."
        )
    }
    
    return enhanced_context

def create_examples_for_bullets(role: str) -> List[Dict[str, str]]:
    """
    Create role-specific examples of good bullet point rewrites.
    
    Args:
        role: Job role title
        
    Returns:
        List of example bullet point rewrites
    """
    # Base examples applicable to most roles
    examples = [
        {
            "original": "Worked on a project to improve system performance",
            "improved": "Optimized system performance by 40% through code refactoring and implementing efficient algorithms"
        },
        {
            "original": "Was responsible for database queries and data retrieval",
            "improved": "Designed and optimized complex SQL queries that reduced data retrieval time by 60% and improved application responsiveness"
        }
    ]
    
    # Add role-specific examples
    role_lower = role.lower()
    
    if "data" in role_lower and ("scien" in role_lower or "analy" in role_lower):
        examples.append({
            "original": "Built predictive models for customer analysis",
            "improved": "Developed machine learning models that predicted customer churn with 92% accuracy, enabling targeted retention efforts that increased retention by 15%"
        })
    elif "developer" in role_lower or "engineer" in role_lower:
        examples.append({
            "original": "Worked on the frontend using React",
            "improved": "Architected and implemented responsive React components that reduced page load time by 35% and improved user engagement metrics by 42%"
        })
    elif "product" in role_lower or "manager" in role_lower:
        examples.append({
            "original": "Led a team to deliver new features",
            "improved": "Led cross-functional team of 8 engineers to deliver 3 key product features ahead of schedule, resulting in 28% increase in user adoption and $1.2M in additional revenue"
        })
    
    return examples 