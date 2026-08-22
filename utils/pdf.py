import io
import re
from typing import Dict, Any, List

# Optional document parsing imports with graceful fallback
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import docx
except ImportError:
    docx = None

def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Extract full raw text from PDF binary data using PyMuPDF or UTF-8 decode fallback."""
    if not fitz:
        return pdf_bytes.decode('utf-8', errors='ignore')
    text_chunks = []
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page in doc:
            text = page.get_text()
            if text:
                text_chunks.append(text)
        doc.close()
    except Exception as e:
        print(f"PyMuPDF Extraction error: {e}")
    return "\n".join(text_chunks)

def extract_text_from_docx_bytes(docx_bytes: bytes) -> str:
    """Extract full raw text from DOCX binary data using python-docx or UTF-8 decode fallback."""
    if not docx:
        return docx_bytes.decode('utf-8', errors='ignore')
    try:
        doc = docx.Document(io.BytesIO(docx_bytes))
        full_text = [para.text for para in doc.paragraphs if para.text]
        return "\n".join(full_text)
    except Exception as e:
        print(f"DOCX Extraction error: {e}")
        return ""

def extract_text_from_file(file_name: str, file_bytes: bytes) -> str:
    """Universal document text extractor supporting PDF, DOCX, and TXT."""
    ext = file_name.lower().split('.')[-1]
    if ext == 'pdf':
        return extract_text_from_pdf_bytes(file_bytes)
    elif ext in ['docx', 'doc']:
        return extract_text_from_docx_bytes(file_bytes)
    elif ext == 'txt':
        return file_bytes.decode('utf-8', errors='ignore')
    else:
        return file_bytes.decode('utf-8', errors='ignore')

def parse_resume_structure(text: str) -> Dict[str, Any]:
    """
    Extract structured candidate data from raw resume text.
    Fallback regex & keyword parsing to ensure fast, reliable results.
    """
    # Extract Email
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    email = email_match.group(0) if email_match else "Not found"

    # Extract Phone Number
    phone_match = re.search(r'(\+\d{1,3}[\s-]?)?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}', text)
    phone = phone_match.group(0) if phone_match else "Not found"

    # Common Skills Taxonomy
    SKILL_KEYWORDS = [
        "python", "java", "c++", "javascript", "typescript", "html", "css", "react", "angular", "vue",
        "node.js", "express", "fastapi", "flask", "django", "sql", "postgresql", "mysql", "mongodb",
        "sqlite", "redis", "qdrant", "pinecone", "chromadb", "aws", "azure", "gcp", "docker", "kubernetes",
        "git", "ci/cd", "machine learning", "deep learning", "nlp", "llm", "rag", "langchain", "llamaindex",
        "pytorch", "tensorflow", "scikit-learn", "pandas", "numpy", "opencv", "devops", "agile", "jira",
        "rest api", "graphql", "microservices", "system design", "data analysis", "tableau", "power bi"
    ]

    text_lower = text.lower()
    found_skills = [skill.title() for skill in SKILL_KEYWORDS if re.search(r'\b' + re.escape(skill) + r'\b', text_lower)]

    # Education Detection
    education_terms = ["b.tech", "b.e", "b.s", "m.tech", "m.s", "bachelor", "master", "phd", "degree", "computer science", "information technology"]
    found_edu = []
    for line in text.split('\n'):
        if any(term in line.lower() for term in education_terms):
            found_edu.append(line.strip())

    education = "; ".join(found_edu[:3]) if found_edu else "Degree in Technical Field"

    # Guess Name (First prominent non-empty line)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    candidate_name = lines[0] if lines and len(lines[0]) < 40 else "Candidate"

    return {
        "candidate_name": candidate_name,
        "email": email,
        "phone": phone,
        "skills": list(set(found_skills)),
        "education": education,
        "raw_text": text
    }
