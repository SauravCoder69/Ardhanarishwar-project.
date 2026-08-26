import os
import sys
import warnings
import logging
from pathlib import Path


class SuppressTransformersStderr:
    def __init__(self, original_stream):
        self.original_stream = original_stream

    def write(self, text):
        if "[ERROR]" in text and ("ImageProcessorKwargs" in text or "docstring" in text or "documented" in text):
            return
        if self.original_stream:
            self.original_stream.write(text)

    def flush(self):
        if self.original_stream and hasattr(self.original_stream, 'flush'):
            self.original_stream.flush()

sys.stderr = SuppressTransformersStderr(sys.stderr)


os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
warnings.filterwarnings("ignore")
logging.getLogger("transformers").setLevel(logging.ERROR)

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "ardhanarishwar.db"
QDRANT_STORAGE_PATH = DATA_DIR / "qdrant_storage"

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
QDRANT_COLLECTION_NAME = "ardhanarishwar_kb"
EMBEDDING_VECTOR_SIZE = 384

KNOWLEDGE_CATEGORIES = [
    "Careers",
    "Education",
    "Training",
    "Interviews",
    "Skills",
    "Recruitment",
    "HR",
    "Business"
]

ADMIN_CATEGORIES = [
    "Global Knowledge",
    "Education",
    "Career",
    "Business",
    "Corporate Finance",
    "Company Strategy",
    "Policies",
    "Training",
    "HR",
    "Recruitment",
    "Operations"
]

CANDIDATE_CATEGORIES = [
    "Resume",
    "Education",
    "Skills",
    "Certifications",
    "Projects",
    "Experience",
    "Career"
]

BUSINESS_CATEGORIES = [
    "Business",
    "HR",
    "Recruitment",
    "Hiring",
    "Company Knowledge",
    "Policies"
]

ROLE_CATEGORIES = {
    "Admin": ADMIN_CATEGORIES,
    "Candidate": CANDIDATE_CATEGORIES,
    "Business": BUSINESS_CATEGORIES,
}

def get_role_categories(role: str):
    """Return the permitted category list for the provided role."""
    return list(ROLE_CATEGORIES.get(role, KNOWLEDGE_CATEGORIES))

# Supported User Roles
ROLE_CANDIDATE = "Candidate"
ROLE_BUSINESS = "Business"
ROLE_ADMIN = "Admin"

ROLES = [ROLE_CANDIDATE, ROLE_BUSINESS, ROLE_ADMIN]

# SaaS Application Branding
APP_NAME = "Ardhanarishwar"
APP_TAGLINE = "One AI Platform for Career Growth, Recruitment & Business Intelligence"
