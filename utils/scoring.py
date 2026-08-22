import re
from typing import List, Dict, Any, Tuple

def calculate_ats_score(resume_text: str, skills: List[str]) -> Dict[str, Any]:
    """
    Calculate an ATS quality score (0-100%) for a resume based on structure, length, and skills.
    """
    score = 50  # Base score
    feedback = []

    # Check Length
    word_count = len(resume_text.split())
    if 250 <= word_count <= 1200:
        score += 15
        feedback.append("Good resume length and density.")
    elif word_count < 250:
        feedback.append("Resume is too short. Add more detailed project and work descriptions.")
    else:
        score += 5
        feedback.append("Resume is quite long. Consider condensing bullet points.")

    # Check Skill Count
    if len(skills) >= 10:
        score += 20
        feedback.append(f"Strong technical skill variety ({len(skills)} skills detected).")
    elif len(skills) >= 5:
        score += 10
        feedback.append("Moderate skill count. Highlight more domain-specific tools.")
    else:
        feedback.append("Low technical skill count. Explicitly list core technologies.")

    # Check Essential Sections
    text_lower = resume_text.lower()
    sections = {
        "Experience": ["experience", "work history", "employment", "internship"],
        "Education": ["education", "degree", "university", "college"],
        "Projects": ["projects", "personal projects", "portfolio"],
        "Skills": ["skills", "technical skills", "competencies"]
    }

    found_sections = 0
    for section_name, keywords in sections.items():
        if any(kw in text_lower for kw in keywords):
            found_sections += 1
        else:
            feedback.append(f"Missing distinct '{section_name}' section heading.")

    score += found_sections * 4
    score = min(100, max(10, score))

    # Generate Strengths & Weaknesses
    strengths = [f for f in feedback if "Good" in f or "Strong" in f or "variety" in f]
    weaknesses = [f for f in feedback if "Missing" in f or "short" in f or "Low" in f]

    if not strengths:
        strengths = ["Structured text layout", "Parseable contact information"]
    if not weaknesses:
        weaknesses = ["Could include quantitative metrics (e.g. Improved performance by 35%)"]

    return {
        "ats_score": round(score, 1),
        "word_count": word_count,
        "skill_count": len(skills),
        "strengths": strengths,
        "weaknesses": weaknesses,
        "formatting_suggestions": [
            "Use clear bullet points starting with action verbs (e.g. Engineered, Developed, Built).",
            "Keep font hierarchy consistent and avoid graphics or columns that disrupt ATS parsers.",
            "Quantify impact wherever possible with percentages, numbers, or time saved."
        ],
        "bullet_point_improvements": [
            "Original: 'Worked on python project for client'",
            "Improved: 'Designed and deployed a scalable Python REST API processing 10k daily requests with 99.9% uptime.'"
        ]
    }

def match_resume_to_jd(resume_skills: List[str], resume_text: str, jd_text: str) -> Dict[str, Any]:
    """
    Compute compatibility match score (0-100%) between a candidate resume and a Job Description.
    """
    # Extract skills from JD
    COMMON_TECH_TERMS = [
        "python", "java", "c++", "javascript", "typescript", "react", "node.js", "express", "fastapi",
        "django", "flask", "sql", "postgresql", "mongodb", "docker", "kubernetes", "aws", "azure", "gcp",
        "machine learning", "deep learning", "nlp", "llm", "rag", "qdrant", "vector db", "git", "ci/cd",
        "rest api", "graphql", "microservices", "system design", "agile", "spark", "hadoop", "tableau"
    ]

    jd_lower = jd_text.lower()
    jd_skills = [s.title() for s in COMMON_TECH_TERMS if re.search(r'\b' + re.escape(s) + r'\b', jd_lower)]

    if not jd_skills:
        jd_skills = ["Python", "SQL", "Git", "Problem Solving"]

    # Calculate skill overlaps
    resume_skills_lower = set([s.lower() for s in resume_skills])
    matching_skills = [s for s in jd_skills if s.lower() in resume_skills_lower]
    missing_skills = [s for s in jd_skills if s.lower() not in resume_skills_lower]

    # Keyword frequency overlap in full text
    jd_words = set(re.findall(r'\w+', jd_lower))
    resume_words = set(re.findall(r'\w+', resume_text.lower()))
    
    if jd_words:
        keyword_match_pct = len(jd_words.intersection(resume_words)) / len(jd_words) * 100
    else:
        keyword_match_pct = 50.0

    skill_match_pct = (len(matching_skills) / len(jd_skills) * 100) if jd_skills else 50.0

    # Weighted Overall Match Score
    overall_match = (skill_match_pct * 0.7) + (keyword_match_pct * 0.3)
    overall_match = min(99.0, max(15.0, round(overall_match, 1)))

    if overall_match >= 80:
        recommendation = "Strong Match"
        recommendation_badge = "🟢 Strong Match"
    elif overall_match >= 60:
        recommendation = "Moderate Match"
        recommendation_badge = "🟡 Moderate Match"
    else:
        recommendation = "Weak Match"
        recommendation_badge = "🔴 Weak Match"

    return {
        "match_score": overall_match,
        "recommendation": recommendation,
        "recommendation_badge": recommendation_badge,
        "matching_skills": matching_skills,
        "missing_skills": missing_skills,
        "required_jd_skills": jd_skills,
        "skill_match_percentage": round(skill_match_pct, 1)
    }

def analyze_skill_gap(current_skills: List[str], target_role: str) -> Dict[str, Any]:
    """
    Generate skill gap breakdown and structured learning recommendations.
    """
    ROLE_REQUIREMENTS = {
        "AI Engineer": ["Python", "PyTorch/TensorFlow", "RAG", "Ollama/LLMs", "Vector DB (Qdrant)", "FastAPI", "Docker", "Cloud (AWS/GCP)", "System Design"],
        "ML Engineer": ["Python", "Scikit-Learn", "Feature Engineering", "MLOps", "Docker", "SQL", "Pandas/NumPy", "Deep Learning"],
        "Python Developer": ["Python", "FastAPI/Django", "PostgreSQL/SQLite", "Git", "REST APIs", "Unit Testing", "Docker"],
        "Data Scientist": ["Python", "R", "SQL", "Pandas", "Data Visualization", "Statistics", "Machine Learning", "A/B Testing"],
        "Full Stack Developer": ["JavaScript", "TypeScript", "React", "Node.js", "HTML/CSS", "SQL/NoSQL", "Git", "CI/CD"]
    }

    target_skills = ROLE_REQUIREMENTS.get(target_role, ["Python", "SQL", "Git", "System Design", "Cloud Basics", "APIs"])
    
    curr_set = set([s.lower() for s in current_skills])
    matching = [s for s in target_skills if s.lower() in curr_set]
    missing = [s for s in target_skills if s.lower() not in curr_set]

    # Generate Learning Priorities
    priorities = []
    for i, skill in enumerate(missing, 1):
        priorities.append({
            "step": i,
            "skill": skill,
            "estimated_weeks": 2 if i <= 2 else 3,
            "focus": f"Mastering {skill} fundamentals and building a demo project."
        })

    return {
        "target_role": target_role,
        "total_target_skills": len(target_skills),
        "matching_skills": matching,
        "missing_skills": missing,
        "completion_percentage": round((len(matching) / len(target_skills) * 100) if target_skills else 0, 1),
        "learning_priorities": priorities
    }
