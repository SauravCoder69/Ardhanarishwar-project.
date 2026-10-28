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

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

# Supported User Roles
ROLE_CANDIDATE = "Candidate"
ROLE_ADMIN = "Admin"

APP_NAME = "Ardhanarishwar"
APP_TAGLINE = "AI Job Aggregator & Career Assistant"
