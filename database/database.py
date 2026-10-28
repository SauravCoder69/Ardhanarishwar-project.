import sqlite3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import DB_PATH
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_password_hasher = PasswordHasher()
_LEGACY_PASSWORD_SALT = "ardhanarishwar_salt_2026"

def get_connection():
    """Establish connection to SQLite database with Row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def hash_password(password: str) -> str:
    """Hash a password with Argon2id."""
    return _password_hasher.hash(password)

def verify_password(password: str, stored_hash: str) -> bool:
    """Verify Argon2id hashes and identify valid legacy SHA-256 hashes."""
    if stored_hash.startswith("$argon2id$"):
        try:
            return _password_hasher.verify(stored_hash, password)
        except VerifyMismatchError:
            return False
    import hashlib
    import hmac

    legacy_hash = hashlib.sha256((password + _LEGACY_PASSWORD_SALT).encode("utf-8")).hexdigest()
    return hmac.compare_digest(stored_hash, legacy_hash)

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
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
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
        user_id INTEGER,
        question TEXT NOT NULL,
        response TEXT NOT NULL,
        rating INTEGER NOT NULL,
        comments TEXT,
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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS aggregated_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT NOT NULL,
        source_id TEXT NOT NULL,
        company_name TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        required_skills TEXT,
        experience TEXT,
        salary TEXT,
        location TEXT,
        job_type TEXT,
        job_url TEXT NOT NULL,
        remote INTEGER NOT NULL DEFAULT 0,
        posted_at TEXT,
        review_status TEXT NOT NULL DEFAULT 'Pending Review',
        admin_note TEXT,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(source, source_id),
        UNIQUE(source, job_url)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS saved_jobs (
        candidate_id INTEGER NOT NULL,
        job_id INTEGER NOT NULL,
        saved_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY(candidate_id, job_id),
        FOREIGN KEY (candidate_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (job_id) REFERENCES aggregated_jobs(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tracked_applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_id INTEGER NOT NULL,
        job_id INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'Saved',
        applied_at DATETIME,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(candidate_id, job_id),
        FOREIGN KEY (candidate_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (job_id) REFERENCES aggregated_jobs(id) ON DELETE CASCADE
    );
    """)

    application_columns = [row[1] for row in cursor.execute("PRAGMA table_info(job_applications);").fetchall()]
    if "resume_path" not in application_columns:
        cursor.execute("ALTER TABLE job_applications ADD COLUMN resume_path TEXT;")

    aggregated_job_columns = [
        row[1] for row in cursor.execute("PRAGMA table_info(aggregated_jobs);").fetchall()
    ]
    if "review_status" not in aggregated_job_columns:
        cursor.execute(
            "ALTER TABLE aggregated_jobs ADD COLUMN review_status TEXT NOT NULL DEFAULT 'Pending Review';"
        )
    if "admin_note" not in aggregated_job_columns:
        cursor.execute("ALTER TABLE aggregated_jobs ADD COLUMN admin_note TEXT;")

    _ensure_feedback_foreign_key(conn)
    _ensure_candidate_profile_foreign_key(conn)

    conn.commit()

    conn.close()

def _ensure_feedback_foreign_key(conn):
    """Add cascading feedback ownership while retaining legacy feedback rows."""
    foreign_keys = conn.execute("PRAGMA foreign_key_list(feedback);").fetchall()
    if any(row["table"] == "users" and row["from"] == "user_id" for row in foreign_keys):
        return

    conn.execute("""
    CREATE TABLE feedback_new (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        question TEXT NOT NULL,
        response TEXT NOT NULL,
        sources TEXT,
        rating INTEGER NOT NULL,
        comments TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)
    conn.execute("""
    INSERT INTO feedback_new (id, user_id, question, response, sources, rating, comments, created_at)
    SELECT f.id,
           CASE WHEN u.id IS NULL THEN NULL ELSE f.user_id END,
           f.question, f.response, f.sources, f.rating, f.comments, f.created_at
    FROM feedback f
    LEFT JOIN users u ON u.id = f.user_id;
    """)
    conn.execute("DROP TABLE feedback;")
    conn.execute("ALTER TABLE feedback_new RENAME TO feedback;")

def _ensure_candidate_profile_foreign_key(conn):
    """Preserve orphaned legacy profiles while allowing real profile cascades."""
    columns = conn.execute("PRAGMA table_info(candidate_profiles);").fetchall()
    user_id_column = next(row for row in columns if row["name"] == "user_id")
    if user_id_column["pk"] == 0:
        return

    conn.execute("""
    CREATE TABLE candidate_profiles_new (
        user_id INTEGER UNIQUE,
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
    conn.execute("""
    INSERT INTO candidate_profiles_new (
        user_id, education, current_skills, experience, career_goal,
        preferred_role, learning_interests, updated_at
    )
    SELECT CASE WHEN u.id IS NULL THEN NULL ELSE p.user_id END,
           p.education, p.current_skills, p.experience, p.career_goal,
           p.preferred_role, p.learning_interests, p.updated_at
    FROM candidate_profiles p
    LEFT JOIN users u ON u.id = p.user_id;
    """)
    conn.execute("DROP TABLE candidate_profiles;")
    conn.execute("ALTER TABLE candidate_profiles_new RENAME TO candidate_profiles;")

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
