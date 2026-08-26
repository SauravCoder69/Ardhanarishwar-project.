import sqlite3
import hashlib
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import DB_PATH

def get_connection():
    """Establish connection to SQLite database with Row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    """Simple SHA-256 password hashing with salt."""
    salt = "ardhanarishwar_salt_2026"
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

def init_db():
    """Initialize database tables if they do not exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        tenant_id TEXT NOT NULL,
        email TEXT,
        full_name TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS candidate_profiles (
        user_id INTEGER PRIMARY KEY,
        education TEXT,
        current_skills TEXT,
        experience TEXT,
        career_goal TEXT,
        preferred_role TEXT,
        learning_interests TEXT,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        tenant_id TEXT NOT NULL,
        role_type TEXT NOT NULL,
        title TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER NOT NULL,
        sender TEXT NOT NULL,
        content TEXT NOT NULL,
        sources TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        document_name TEXT NOT NULL,
        category TEXT NOT NULL,
        source TEXT,
        tenant_id TEXT NOT NULL,
        uploaded_by INTEGER,
        chunk_count INTEGER DEFAULT 0,
        uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mock_interviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        job_role TEXT NOT NULL,
        experience_level TEXT,
        difficulty TEXT,
        interview_type TEXT,
        score_overall REAL,
        score_technical REAL,
        score_communication REAL,
        summary_feedback TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resume_analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        resume_name TEXT NOT NULL,
        ats_score REAL,
        target_job TEXT,
        match_score REAL,
        extracted_skills TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        question TEXT NOT NULL,
        response TEXT NOT NULL,
        sources TEXT,
        rating INTEGER NOT NULL,
        comments TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS unanswered_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        tenant_id TEXT NOT NULL,
        question TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Pending',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        business_id INTEGER NOT NULL,
        tenant_id TEXT NOT NULL,
        company_name TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        required_skills TEXT,
        experience TEXT,
        salary TEXT,
        location TEXT,
        job_type TEXT,
        status TEXT NOT NULL DEFAULT 'Pending Approval',
        admin_note TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (business_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS job_applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        candidate_id INTEGER NOT NULL,
        resume_name TEXT,
        resume_path TEXT,
        cover_message TEXT,
        status TEXT NOT NULL DEFAULT 'Applied',
        applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(job_id, candidate_id),
        FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
        FOREIGN KEY (candidate_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    application_columns = [row[1] for row in cursor.execute("PRAGMA table_info(job_applications);").fetchall()]
    if "resume_path" not in application_columns:
        cursor.execute("ALTER TABLE job_applications ADD COLUMN resume_path TEXT;")

    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM users;")
    if cursor.fetchone()[0] == 0:
        default_admin = ("admin", hash_password("admin123"), "Admin", "tenant_global", "admin@ardhanarishwar.ai", "System Admin")
        default_candidate = ("candidate", hash_password("cand123"), "Candidate", "tenant_cand_1", "candidate@example.com", "John Doe")
        default_business = ("business", hash_password("biz123"), "Business", "tenant_biz_1", "hr@techcorp.com", "TechCorp HR")
        
        cursor.execute("INSERT INTO users (username, password_hash, role, tenant_id, email, full_name) VALUES (?, ?, ?, ?, ?, ?);", default_admin)
        cursor.execute("INSERT INTO users (username, password_hash, role, tenant_id, email, full_name) VALUES (?, ?, ?, ?, ?, ?);", default_candidate)
        cursor.execute("INSERT INTO users (username, password_hash, role, tenant_id, email, full_name) VALUES (?, ?, ?, ?, ?, ?);", default_business)
        
        conn.commit()

        # Seed initial candidate profile for default candidate (user_id 2)
        cursor.execute("""
        INSERT INTO candidate_profiles (user_id, education, current_skills, experience, career_goal, preferred_role, learning_interests)
        VALUES (2, 'B.Tech Computer Science', 'Python, SQL, Machine Learning, HTML, CSS', '2 Years as Junior Data Scientist', 'AI Engineer', 'Senior AI Developer', 'RAG, FastApi, Ollama, Vector DBs, System Design');
        """)
        conn.commit()

    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
