import sqlite3
from database.database import get_connection, hash_password
from database.database import verify_password
from typing import List, Dict, Optional, Any

def _account_has_role(conn, current_user: Optional[Dict[str, Any]], role: str) -> bool:
    if not current_user or current_user.get("role") != role or not current_user.get("id"):
        return False
    cursor = conn.execute("SELECT role, tenant_id FROM users WHERE id = ?;", (current_user["id"],))
    account = cursor.fetchone()
    return bool(
        account
        and account["role"] == role
        and account["tenant_id"] == current_user.get("tenant_id")
    )

def user_matches_tenant(user_id: int, tenant_id: str, role: str) -> bool:
    """Verify that a database account's role and tenant match the request context."""
    conn = get_connection()
    account = conn.execute(
        "SELECT role, tenant_id FROM users WHERE id = ?;",
        (user_id,)
    ).fetchone()
    conn.close()
    return bool(account and account["role"] == role and account["tenant_id"] == tenant_id)

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate user with username and password."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?;", (username,))
    user = cursor.fetchone()
    if user and verify_password(password, user["password_hash"]):
        if not user["password_hash"].startswith("$argon2id$"):
            cursor.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?;",
                (hash_password(password), user["id"])
            )
            conn.commit()
        authenticated_user = dict(user)
        authenticated_user.pop("password_hash", None)
    else:
        authenticated_user = None
    conn.close()
    return authenticated_user

def change_password(user_id: int, current_password: str, new_password: str) -> bool:
    """Change a user's password after verifying the current password."""
    if len(new_password) < 8:
        return False

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE id = ?;", (user_id,))
    user = cursor.fetchone()
    if not user or not verify_password(current_password, user["password_hash"]):
        conn.close()
        return False

    cursor.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?;",
        (hash_password(new_password), user_id)
    )
    changed = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return changed

def create_user(username: str, password: str, role: str, tenant_id: str, email: str = "", full_name: str = "") -> Optional[int]:
    """Register a new user in the database."""
    if role != "Candidate" or not username.strip() or len(password) < 8 or not tenant_id.strip():
        return None

    conn = get_connection()
    cursor = conn.cursor()
    pwd_hash = hash_password(password)
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash, role, tenant_id, email, full_name) VALUES (?, ?, ?, ?, ?, ?);",
            (username, pwd_hash, role, tenant_id, email, full_name)
        )
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        return None

def get_all_users(current_user: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Retrieve all registered users for Admin panel."""
    conn = get_connection()
    if not _account_has_role(conn, current_user, "Admin"):
        conn.close()
        raise PermissionError("Only administrators can list user accounts.")
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role, tenant_id, email, full_name, created_at FROM users ORDER BY id DESC;")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_user(current_user: Optional[Dict[str, Any]], user_id: int) -> bool:
    """Delete a user only when requested by an Admin, excluding the active account."""
    if not current_user or current_user.get("role") != "Admin" or current_user.get("id") == user_id:
        return False

    conn = get_connection()
    cursor = conn.cursor()
    if not _account_has_role(conn, current_user, "Admin"):
        conn.close()
        return False
    cursor.execute("DELETE FROM users WHERE id = ?;", (user_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def get_candidate_profile(user_id: int) -> Dict[str, Any]:
    """Get profile memory for a candidate."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM candidate_profiles WHERE user_id = ?;", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return {
        "user_id": user_id,
        "education": "",
        "current_skills": "",
        "experience": "",
        "career_goal": "",
        "preferred_role": "",
        "learning_interests": ""
    }

def save_candidate_profile(user_id: int, education: str, current_skills: str, experience: str, career_goal: str, preferred_role: str, learning_interests: str):
    """Save or update candidate profile facts."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO candidate_profiles (user_id, education, current_skills, experience, career_goal, preferred_role, learning_interests, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(user_id) DO UPDATE SET
        education = excluded.education,
        current_skills = excluded.current_skills,
        experience = excluded.experience,
        career_goal = excluded.career_goal,
        preferred_role = excluded.preferred_role,
        learning_interests = excluded.learning_interests,
        updated_at = CURRENT_TIMESTAMP;
    """, (user_id, education, current_skills, experience, career_goal, preferred_role, learning_interests))
    conn.commit()
    conn.close()

def create_conversation(user_id: int, tenant_id: str, role_type: str, title: str = "New Conversation") -> int:
    """Create a new chat conversation session."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO conversations (user_id, tenant_id, role_type, title) VALUES (?, ?, ?, ?);", (user_id, tenant_id, role_type, title))
    conv_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return conv_id

def get_user_conversations(user_id: int) -> List[Dict[str, Any]]:
    """Fetch active conversations for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM conversations WHERE user_id = ? ORDER BY id DESC;", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_message(conversation_id: int, sender: str, content: str):
    """Save user or assistant chat message."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (conversation_id, sender, content) VALUES (?, ?, ?);",
        (conversation_id, sender, content)
    )
    conn.commit()
    conn.close()

def get_conversation_messages(conversation_id: int) -> List[Dict[str, Any]]:
    """Retrieve full message history for a conversation."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, conversation_id, sender, content, created_at "
        "FROM messages WHERE conversation_id = ? ORDER BY id ASC;",
        (conversation_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def save_mock_interview(user_id: int, job_role: str, experience_level: str, difficulty: str, interview_type: str, score_overall: float, score_technical: float, score_communication: float, summary_feedback: str):
    """Store finished mock interview summary."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO mock_interviews (user_id, job_role, experience_level, difficulty, interview_type, score_overall, score_technical, score_communication, summary_feedback)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (user_id, job_role, experience_level, difficulty, interview_type, score_overall, score_technical, score_communication, summary_feedback))
    conn.commit()
    conn.close()

def get_user_interviews(user_id: int) -> List[Dict[str, Any]]:
    """Get history of interviews for a candidate."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM mock_interviews WHERE user_id = ? ORDER BY created_at DESC;", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_resume_analysis(user_id: int, resume_name: str, ats_score: float, target_job: str, match_score: float, extracted_skills: str):
    """Store resume evaluation record."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO resume_analyses (user_id, resume_name, ats_score, target_job, match_score, extracted_skills)
    VALUES (?, ?, ?, ?, ?, ?);
    """, (user_id, resume_name, ats_score, target_job, match_score, extracted_skills))
    conn.commit()
    conn.close()

def record_feedback(
    current_user: Dict[str, Any],
    question: str,
    response: str,
    rating: int,
    comments: str = "",
) -> bool:
    """Save feedback submitted by the owning candidate account."""
    if rating not in (-1, 1):
        return False
    conn = get_connection()
    cursor = conn.cursor()
    if not _account_has_role(conn, current_user, "Candidate"):
        conn.close()
        return False
    cursor.execute("""
    INSERT INTO feedback (user_id, question, response, rating, comments)
    VALUES (?, ?, ?, ?, ?);
    """, (current_user["id"], question, response, rating, comments))
    conn.commit()
    conn.close()
    return True

def get_feedback_stats(current_user: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Calculate positive vs negative feedback percentages for Admin dashboard."""
    conn = get_connection()
    if not _account_has_role(conn, current_user, "Admin"):
        conn.close()
        raise PermissionError("Only administrators can view feedback records.")
    cursor = conn.cursor()
    cursor.execute("SELECT rating, COUNT(*) as cnt FROM feedback GROUP BY rating;")
    rows = cursor.fetchall()
    
    cursor.execute("SELECT question, response, rating, comments, created_at FROM feedback ORDER BY id DESC LIMIT 10;")
    recent = [dict(r) for r in cursor.fetchall()]
    conn.close()

    total = sum(r['cnt'] for r in rows)
    positives = sum(r['cnt'] for r in rows if r['rating'] == 1)
    negatives = sum(r['cnt'] for r in rows if r['rating'] == -1)

    pos_pct = round((positives / total * 100), 1) if total > 0 else 100.0
    neg_pct = round((negatives / total * 100), 1) if total > 0 else 0.0

    return {
        "total_feedback": total,
        "positive_count": positives,
        "negative_count": negatives,
        "positive_pct": pos_pct,
        "negative_pct": neg_pct,
        "recent_feedback": recent
    }

def get_jobs(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve legacy job posts with an optional status filter."""
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM jobs WHERE 1 = 1"
    params = []
    if status:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY created_at DESC;"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_job_status(current_user: Dict[str, Any], job_id: int, status: str, admin_note: str = "") -> bool:
    """Approve, reject, close, or archive a job posting."""
    conn = get_connection()
    cursor = conn.cursor()
    if not _account_has_role(conn, current_user, "Admin"):
        conn.close()
        return False
    cursor.execute("""
    UPDATE jobs SET status = ?, admin_note = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?;
    """, (status, admin_note, job_id))
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated

def apply_to_job(job_id: int, current_user: Dict[str, Any], resume_name: str, cover_message: str, resume_path: str = "") -> bool:
    """Submit one application per candidate for an approved job."""
    conn = get_connection()
    cursor = conn.cursor()
    if not _account_has_role(conn, current_user, "Candidate"):
        conn.close()
        return False
    if not cursor.execute(
        "SELECT 1 FROM jobs WHERE id = ? AND status = 'Approved';",
        (job_id,)
    ).fetchone():
        conn.close()
        return False
    try:
        cursor.execute("""
        INSERT INTO job_applications (job_id, candidate_id, resume_name, resume_path, cover_message)
        VALUES (?, ?, ?, ?, ?);
        """, (job_id, current_user["id"], resume_name, resume_path, cover_message))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def has_applied(job_id: int, candidate_id: int) -> bool:
    """Check whether a candidate already applied to a job."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM job_applications WHERE job_id = ? AND candidate_id = ?;", (job_id, candidate_id))
    applied = cursor.fetchone() is not None
    conn.close()
    return applied

def get_candidate_applications(current_user: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Retrieve a candidate's submitted applications."""
    conn = get_connection()
    cursor = conn.cursor()
    if not _account_has_role(conn, current_user, "Candidate"):
        conn.close()
        return []
    cursor.execute("""
    SELECT a.*, j.company_name, j.title, j.location
    FROM job_applications a JOIN jobs j ON j.id = a.job_id
    WHERE a.candidate_id = ? ORDER BY a.applied_at DESC;
    """, (current_user["id"],))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_job_applications(current_user: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Retrieve all candidate applications for an authenticated administrator."""
    conn = get_connection()
    cursor = conn.cursor()
    if not _account_has_role(conn, current_user, "Admin"):
        conn.close()
        raise PermissionError("Only administrators can view all applications.")
    query = """
    SELECT a.*, j.company_name, j.title, j.business_id, j.tenant_id,
           u.full_name, u.email, u.username
    FROM job_applications a
    JOIN jobs j ON j.id = a.job_id
    JOIN users u ON u.id = a.candidate_id
    """
    query += " ORDER BY a.applied_at DESC;"
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_application_status(current_user: Optional[Dict[str, Any]], application_id: int, status: str) -> bool:
    """Update candidate application status (e.g. Shortlisted, Interview Scheduled, Rejected)."""
    conn = get_connection()
    cursor = conn.cursor()
    if not _account_has_role(conn, current_user, "Admin"):
        conn.close()
        return False
    cursor.execute("""
    UPDATE job_applications SET status = ? WHERE id = ?;
    """, (status, application_id))
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated

def get_system_metrics(current_user: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Retrieve high-level metrics for Admin Dashboard."""
    conn = get_connection()
    if not _account_has_role(conn, current_user, "Admin"):
        conn.close()
        raise PermissionError("Only administrators can view platform metrics.")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users;")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'Candidate';")
    total_candidates = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM messages;")
    total_messages = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM resume_analyses;")
    total_resume_analyses = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM mock_interviews;")
    total_interviews = cursor.fetchone()[0]

    conn.close()

    return {
        "total_users": total_users,
        "candidates": total_candidates,
        "conversations": total_messages,
        "resume_analyses": total_resume_analyses,
        "mock_interviews": total_interviews
    }

def get_dashboard_metrics(
    user_id: int,
    role: str,
    tenant_id: str,
    current_user: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Retrieve metrics scoped to the current role, except for the Admin view."""
    conn = get_connection()
    if role not in ("Candidate", "Admin"):
        conn.close()
        raise PermissionError("Candidate metrics are not available to this account.")
    if (
        not current_user
        or current_user.get("id") != user_id
        or current_user.get("tenant_id") != tenant_id
        or not _account_has_role(conn, current_user, role)
    ):
        conn.close()
        raise PermissionError("Metrics are available only to the authenticated account.")
    if role == "Admin":
        conn.close()
        return get_system_metrics(current_user)

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM conversations WHERE user_id = ?;", (user_id,))
    conversations = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM resume_analyses WHERE user_id = ?;", (user_id,))
    resume_analyses = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM mock_interviews WHERE user_id = ?;", (user_id,))
    mock_interviews = cursor.fetchone()[0]
    conn.close()
    return {
        "conversations": conversations,
        "resume_analyses": resume_analyses,
        "mock_interviews": mock_interviews,
    }

def upsert_aggregated_jobs(jobs: List[Dict[str, Any]]) -> int:
    """Insert or refresh listings without overwriting their moderation decisions."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany("""
    INSERT INTO aggregated_jobs (
        source, source_id, company_name, title, description, required_skills,
        experience, salary, location, job_type, job_url, remote, posted_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT DO UPDATE SET
        company_name = excluded.company_name,
        title = excluded.title,
        description = excluded.description,
        required_skills = excluded.required_skills,
        experience = excluded.experience,
        salary = excluded.salary,
        location = excluded.location,
        job_type = excluded.job_type,
        job_url = excluded.job_url,
        remote = excluded.remote,
        posted_at = excluded.posted_at,
        updated_at = CURRENT_TIMESTAMP;
    """, [
        (
            job["source"], job["source_id"], job["company_name"], job["title"],
            job["description"], job.get("required_skills", ""), job.get("experience", ""),
            job.get("salary", ""), job.get("location", ""), job.get("job_type", ""),
            job["job_url"], int(bool(job.get("remote"))), job.get("posted_at", "")
        )
        for job in jobs
    ])
    conn.commit()
    updated = cursor.rowcount
    conn.close()
    return updated

def search_aggregated_jobs(
    role: str = "",
    location: str = "",
    skills: str = "",
    experience: str = "",
    job_type: str = "",
    query: str = "",
) -> List[Dict[str, Any]]:
    """Search cached listings using validated, parameterized candidate filters."""
    conn = get_connection()
    conditions = []
    params = []
    if query.strip():
        searchable_columns = ("title", "company_name", "required_skills", "description", "location", "source")
        conditions.append("(" + " OR ".join(f"lower({column}) LIKE ?" for column in searchable_columns) + ")")
        params.extend([f"%{query.strip().lower()}%"] * len(searchable_columns))
    for column, value in (
        ("title", role),
        ("location", location),
        ("experience", experience),
    ):
        if value.strip():
            conditions.append(f"lower({column}) LIKE ?")
            params.append(f"%{value.strip().lower()}%")
    skill_filters = [skill.strip() for skill in skills.split(",") if skill.strip()]
    for skill in skill_filters:
        conditions.append("lower(required_skills) LIKE ?")
        params.append(f"%{skill.lower()}%")
    if job_type.strip().lower() == "remote":
        conditions.append("(remote = 1 OR lower(job_type) LIKE ?)")
        params.append("%remote%")
    elif job_type.strip():
        conditions.append("lower(job_type) LIKE ?")
        params.append(f"%{job_type.strip().lower()}%")
    conditions.append("review_status = 'Approved'")
    where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    rows = conn.execute(
        f"SELECT * FROM aggregated_jobs{where_clause} ORDER BY posted_at DESC, id DESC LIMIT 200;",
        params
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def save_aggregated_job(current_user: Dict[str, Any], job_id: int) -> bool:
    """Save an approved listing for the owning candidate and add it to tracking."""
    conn = get_connection()
    cursor = conn.cursor()
    if not _account_has_role(conn, current_user, "Candidate"):
        conn.close()
        return False
    if not cursor.execute(
        "SELECT 1 FROM aggregated_jobs WHERE id = ? AND review_status = 'Approved';",
        (job_id,)
    ).fetchone():
        conn.close()
        return False
    cursor.execute(
        "INSERT OR IGNORE INTO saved_jobs (candidate_id, job_id) VALUES (?, ?);",
        (current_user["id"], job_id)
    )
    cursor.execute(
        "INSERT OR IGNORE INTO tracked_applications (candidate_id, job_id) VALUES (?, ?);",
        (current_user["id"], job_id)
    )
    saved = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return saved

def get_aggregated_jobs_for_review(current_user: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Retrieve external listings for an authenticated administrator to review."""
    conn = get_connection()
    if not _account_has_role(conn, current_user, "Admin"):
        conn.close()
        raise PermissionError("Only administrators can review external job listings.")
    rows = conn.execute("""
    SELECT * FROM aggregated_jobs
    ORDER BY CASE review_status
        WHEN 'Pending Review' THEN 0
        WHEN 'Approved' THEN 1
        WHEN 'Rejected' THEN 2
        WHEN 'Closed' THEN 3
        ELSE 4
    END, updated_at DESC, id DESC;
    """).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_aggregated_job_status(
    current_user: Optional[Dict[str, Any]],
    job_id: int,
    status: str,
    admin_note: str = "",
) -> bool:
    """Update an external listing's moderation status as an authenticated admin."""
    allowed_statuses = {"Pending Review", "Approved", "Rejected", "Closed"}
    if status not in allowed_statuses:
        return False
    conn = get_connection()
    if not _account_has_role(conn, current_user, "Admin"):
        conn.close()
        return False
    cursor = conn.execute("""
    UPDATE aggregated_jobs
    SET review_status = ?, admin_note = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?;
    """, (status, admin_note, job_id))
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated

def get_tracked_applications(current_user: Dict[str, Any]) -> List[Dict[str, Any]]:
    """List only the authenticated candidate's saved external jobs and status."""
    conn = get_connection()
    if not _account_has_role(conn, current_user, "Candidate"):
        conn.close()
        return []
    rows = conn.execute("""
    SELECT t.id, t.status, t.applied_at, t.updated_at,
           j.id AS job_id, j.source, j.company_name, j.title, j.location,
           j.job_type, j.job_url, j.posted_at
    FROM tracked_applications t
    JOIN aggregated_jobs j ON j.id = t.job_id
    WHERE t.candidate_id = ? AND j.review_status = 'Approved'
    ORDER BY t.updated_at DESC;
    """, (current_user.get("id"),)).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_tracked_application(current_user: Dict[str, Any], job_id: int, status: str) -> bool:
    """Update an external job's application status for its owning candidate only."""
    allowed_statuses = {"Saved", "Applied", "Interview", "Offer", "Rejected", "Closed"}
    if status not in allowed_statuses:
        return False
    conn = get_connection()
    cursor = conn.cursor()
    if not _account_has_role(conn, current_user, "Candidate"):
        conn.close()
        return False
    if status == "Applied":
        cursor.execute("""
        UPDATE tracked_applications
        SET status = ?, applied_at = COALESCE(applied_at, CURRENT_TIMESTAMP),
            updated_at = CURRENT_TIMESTAMP
        WHERE candidate_id = ? AND job_id = ?;
        """, (status, current_user.get("id"), job_id))
    else:
        cursor.execute("""
        UPDATE tracked_applications
        SET status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE candidate_id = ? AND job_id = ?;
        """, (status, current_user.get("id"), job_id))
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated
