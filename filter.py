"""
filter.py
Keyword-based job filter — keeps only AI/ML/Data/SDE roles.
"""

KEYWORDS = [
    "AI",
    "Artificial Intelligence",
    "Machine Learning",
    "ML",
    "Deep Learning",
    "Data",
    "Data Science",
    "Data Engineer",
    "Data Analyst",
    "SDE",
    "Software Engineer",
    "Software Developer",
    "Software Development",
    "Backend",
    "Backend Engineer",
    "Frontend",
    "Frontend Engineer",
    "Full Stack",
    "Fullstack",
    "NLP",
    "Computer Vision",
    "GenAI",
    "LLM",
]


def is_relevant(title: str) -> bool:
    """
    Return True if the job title contains at least one target keyword.
    Case-insensitive match.
    """
    title_lower = title.lower()
    return any(keyword.lower() in title_lower for keyword in KEYWORDS)
