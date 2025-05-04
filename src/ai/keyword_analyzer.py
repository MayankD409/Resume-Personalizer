"""
This module analyzes keyword matching between job descriptions and resumes,
providing metrics on how well the resume matches the job requirements.
"""
from typing import Dict, List, Tuple, Set
import re
import string
import spacy
from collections import Counter
import logging

logger = logging.getLogger(__name__)

# Load spaCy language model (or use a lightweight version)
try:
    nlp = spacy.load("en_core_web_sm")
except:
    logger.warning("Could not load spaCy model. Will use basic keyword extraction.")
    nlp = None

# Common stop words to filter out
STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "else", "when", "at", "from", "by", "for",
    "with", "about", "against", "between", "into", "through", "during", "before", "after", "above",
    "below", "to", "of", "in", "on", "off", "over", "under", "again", "further", "then", "once",
    "here", "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more",
    "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", 
    "very", "s", "t", "can", "will", "just", "should", "now"
}

def extract_keywords(text: str, min_length: int = 3, top_n: int = 50) -> List[str]:
    """
    Extract the most important keywords from text using NLP techniques.
    
    Args:
        text: The text to analyze
        min_length: Minimum word length to consider
        top_n: Number of top keywords to return
        
    Returns:
        List of keywords ordered by importance
    """
    if nlp:
        # Use spaCy for better keyword extraction
        doc = nlp(text)
        
        # Extract noun phrases and named entities
        keywords = []
        
        # Get noun phrases
        for chunk in doc.noun_chunks:
            keywords.append(chunk.text.lower())
            
        # Get named entities
        for ent in doc.ents:
            keywords.append(ent.text.lower())
            
        # Get individual tokens that are nouns, verbs, or adjectives
        for token in doc:
            if token.pos_ in ["NOUN", "PROPN", "VERB", "ADJ"] and len(token.text) >= min_length:
                if not token.is_stop and not token.is_punct:
                    keywords.append(token.text.lower())
        
        # Count occurrences and get top keywords
        keyword_counter = Counter(keywords)
        return [keyword for keyword, _ in keyword_counter.most_common(top_n)]
    else:
        # Fallback to basic keyword extraction
        # Remove punctuation and split into words
        text = text.lower()
        text = re.sub(r'[' + string.punctuation + ']', ' ', text)
        words = text.split()
        
        # Filter out stop words and short words
        filtered_words = [word for word in words if word not in STOP_WORDS and len(word) >= min_length]
        
        # Count occurrences and get top keywords
        word_counter = Counter(filtered_words)
        return [word for word, _ in word_counter.most_common(top_n)]

def analyze_keyword_match(jd_text: str, resume_text: str) -> Dict:
    """
    Analyze how well the resume matches the job description based on keywords.
    
    Args:
        jd_text: Job description text
        resume_text: Resume text
        
    Returns:
        Dictionary with match metrics
    """
    # Extract keywords from both texts
    jd_keywords = extract_keywords(jd_text)
    resume_keywords = extract_keywords(resume_text)
    
    # Convert to sets for overlap analysis
    jd_keywords_set = set(jd_keywords)
    resume_keywords_set = set(resume_keywords)
    
    # Find matched and missing keywords
    matched_keywords = jd_keywords_set.intersection(resume_keywords_set)
    missing_keywords = jd_keywords_set - resume_keywords_set
    
    # Calculate match percentage
    match_percentage = (len(matched_keywords) / len(jd_keywords_set)) * 100 if jd_keywords_set else 0
    
    # Create keyword match report
    return {
        "match_percentage": round(match_percentage, 2),
        "matched_keywords": list(matched_keywords),
        "missing_keywords": list(missing_keywords)[:20],  # Limit to top 20 missing
        "top_jd_keywords": jd_keywords[:20],
        "top_resume_keywords": resume_keywords[:20]
    }

def get_keyword_recommendations(jd_text: str, resume_text: str) -> List[str]:
    """
    Generate prioritized recommendations for keywords to add to the resume.
    
    Args:
        jd_text: Job description text
        resume_text: Resume text
        
    Returns:
        List of recommended keywords to add, in priority order
    """
    # Extract keywords from both texts
    jd_keywords = extract_keywords(jd_text)
    resume_keywords = extract_keywords(resume_text)
    
    # Convert to sets for overlap analysis
    jd_keywords_set = set(jd_keywords)
    resume_keywords_set = set(resume_keywords)
    
    # Find missing keywords
    missing_keywords = jd_keywords_set - resume_keywords_set
    
    # Count occurrences in the original JD text to determine importance
    jd_text_lower = jd_text.lower()
    keyword_importance = {}
    
    for keyword in missing_keywords:
        # Count occurrences of the keyword
        count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', jd_text_lower))
        # Check if keyword is in the first paragraph (higher importance)
        first_paragraph = jd_text_lower.split('\n\n')[0] if '\n\n' in jd_text_lower else jd_text_lower
        in_first_para = keyword in first_paragraph
        
        # Calculate importance score
        importance = count + (2 if in_first_para else 0)
        keyword_importance[keyword] = importance
    
    # Sort by importance
    sorted_keywords = sorted(missing_keywords, key=lambda k: keyword_importance.get(k, 0), reverse=True)
    
    return sorted_keywords[:15]  # Return top 15 recommendations

def format_keyword_report(analysis: Dict, colorize: bool = True) -> str:
    """
    Format keyword analysis into a readable report.
    
    Args:
        analysis: Keyword analysis dict from analyze_keyword_match
        colorize: Whether to add terminal colors
        
    Returns:
        Formatted report string
    """
    match_percentage = analysis["match_percentage"]
    
    # Define color codes
    green = "\033[32m" if colorize else ""
    yellow = "\033[33m" if colorize else ""
    red = "\033[31m" if colorize else ""
    reset = "\033[0m" if colorize else ""
    
    # Determine match quality
    if match_percentage >= 70:
        match_color = green
        match_desc = "EXCELLENT"
    elif match_percentage >= 50:
        match_color = yellow
        match_desc = "GOOD"
    else:
        match_color = red
        match_desc = "NEEDS IMPROVEMENT"
    
    # Build report
    report = []
    report.append(f"🔍 KEYWORD MATCH ANALYSIS")
    report.append(f"Overall match: {match_color}{match_percentage:.1f}% ({match_desc}){reset}")
    report.append("")
    
    # Top matched keywords
    matched = ", ".join(analysis["matched_keywords"][:10])
    report.append(f"{green}✓ Matched Keywords:{reset} {matched}")
    
    # Missing keywords
    if analysis["missing_keywords"]:
        missing = ", ".join(analysis["missing_keywords"][:10])
        report.append(f"{red}✗ Missing Keywords:{reset} {missing}")
    
    return "\n".join(report) 