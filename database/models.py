import json
from database.database import get_connection, hash_password
from typing import List, Dict, Optional, Any

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate user with username and password."""
    conn = get_connection()
    cursor = conn.cursor()
    pwd_hash = hash_password(password)
    cursor.execute("SELECT * FROM users WHERE username = ? AND password_hash = ?;", (username, pwd_hash))
    user = cursor.fetchone()
    conn.close()
    if user:
        return dict(user)
    return None

def change_password(user_id: int, current_password: str, new_password: str) -> bool:
    """Change a user's password after verifying the current password."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM users WHERE id = ? AND password_hash = ?;",
        (user_id, hash_password(current_password))
    )
    if not cursor.fetchone():
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
    except Exception as e:
        conn.close()
        print(f"Error creating user: {e}")
        return None

def get_all_users() -> List[Dict[str, Any]]:
    """Retrieve all registered users for Admin panel."""
    conn = get_connection()
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

def save_message(conversation_id: int, sender: str, content: str, sources: Optional[List[Dict[str, Any]]] = None):
    """Save user or assistant chat message."""
    conn = get_connection()
    cursor = conn.cursor()
    sources_json = json.dumps(sources) if sources else ""
    cursor.execute("INSERT INTO messages (conversation_id, sender, content, sources) VALUES (?, ?, ?, ?);", (conversation_id, sender, content, sources_json))
    conn.commit()
    conn.close()

def get_conversation_messages(conversation_id: int) -> List[Dict[str, Any]]:
    """Retrieve full message history for a conversation."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messages WHERE conversation_id = ? ORDER BY id ASC;", (conversation_id,))
    rows = cursor.fetchall()
    conn.close()
    messages = []
    for r in rows:
        d = dict(r)
        d['sources'] = json.loads(d['sources']) if d.get('sources') else []
        messages.append(d)
    return messages

def register_document(doc_id: str, document_name: str, category: str, source: str, tenant_id: str, uploaded_by: int, chunk_count: int):
    """Save uploaded document metadata in SQLite."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO documents (id, document_name, category, source, tenant_id, uploaded_by, chunk_count)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """, (doc_id, document_name, category, source, tenant_id, uploaded_by, chunk_count))
    conn.commit()
    conn.close()

def get_document_by_id(doc_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a single document record by document id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE id = ?;", (doc_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def can_delete_document(user: Optional[Dict[str, Any]], document: Optional[Dict[str, Any]]) -> bool:
    """Return whether the current user is allowed to delete the document."""
    if not user or not document:
        return False

    role = user.get("role")
    user_id = user.get("id")
    tenant_id = user.get("tenant_id")

    if role == "Admin":
        return True

    if role == "Candidate":
        return (
            document.get("tenant_id") == tenant_id and
            document.get("uploaded_by") == user_id
        )

    if role == "Business":
        return (
            document.get("tenant_id") == tenant_id or
            (
                document.get("tenant_id") == "tenant_global" and
                document.get("uploaded_by") == user_id
            )
        )

    return False

def get_all_documents() -> List[Dict[str, Any]]:
    """Retrieve all uploaded knowledge base documents."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents ORDER BY uploaded_at DESC;")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_document_record(doc_id: str):
    """Delete document metadata record by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM documents WHERE id = ?;", (doc_id,))
    conn.commit()
    conn.close()

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

def record_feedback(user_id: int, question: str, response: str, rating: int, sources: str = "", comments: str = ""):
    """Save user response rating (+1 or -1)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO feedback (user_id, question, response, rating, sources, comments)
    VALUES (?, ?, ?, ?, ?, ?);
    """, (user_id, question, response, rating, sources, comments))
    conn.commit()
    conn.close()

def get_feedback_stats() -> Dict[str, Any]:
    """Calculate positive vs negative feedback percentages for Admin dashboard."""
    conn = get_connection()
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

def record_unanswered_question(user_id: int, tenant_id: str, question: str):
    """Record a candidate question that had no relevant RAG information."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO unanswered_questions (user_id, tenant_id, question) VALUES (?, ?, ?);",
        (user_id, tenant_id, question.strip())
    )
    conn.commit()
    conn.close()

def get_unanswered_questions(status: str = "Pending") -> List[Dict[str, Any]]:
    """Retrieve unanswered candidate questions for the Admin dashboard."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT q.id, q.question, q.status, q.created_at,
           u.full_name, u.username, u.email, q.tenant_id
    FROM unanswered_questions q
    JOIN users u ON u.id = q.user_id
    WHERE q.status = ?
    ORDER BY q.created_at DESC;
    """, (status,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def mark_unanswered_question_resolved(question_id: int) -> bool:
    """Mark an Admin-reviewed unanswered question as resolved."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE unanswered_questions SET status = 'Resolved' WHERE id = ?;",
        (question_id,)
    )
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated

def create_job(business_id: int, tenant_id: str, company_name: str, title: str, description: str,
               required_skills: str, experience: str, salary: str, location: str, job_type: str) -> int:
    """Create a job posting awaiting Admin approval."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO jobs (business_id, tenant_id, company_name, title, description,
                      required_skills, experience, salary, location, job_type)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (business_id, tenant_id, company_name, title, description, required_skills,
          experience, salary, location, job_type))
    job_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return job_id

def get_jobs(status: Optional[str] = None, business_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Retrieve jobs with optional status and owner filters."""
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM jobs WHERE 1 = 1"
    params = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if business_id:
        query += " AND business_id = ?"
        params.append(business_id)
    query += " ORDER BY created_at DESC;"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_job_status(job_id: int, status: str, admin_note: str = "") -> bool:
    """Approve, reject, close, or archive a job posting."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE jobs SET status = ?, admin_note = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?;
    """, (status, admin_note, job_id))
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated

def apply_to_job(job_id: int, candidate_id: int, resume_name: str, cover_message: str, resume_path: str = "") -> bool:
    """Submit one application per candidate for an approved job."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO job_applications (job_id, candidate_id, resume_name, resume_path, cover_message)
        VALUES (?, ?, ?, ?, ?);
        """, (job_id, candidate_id, resume_name, resume_path, cover_message))
        conn.commit()
        return True
    except Exception:
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

def get_candidate_applications(candidate_id: int) -> List[Dict[str, Any]]:
    """Retrieve a candidate's submitted applications."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT a.*, j.company_name, j.title, j.location
    FROM job_applications a JOIN jobs j ON j.id = a.job_id
    WHERE a.candidate_id = ? ORDER BY a.applied_at DESC;
    """, (candidate_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_job_applications(business_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Retrieve applications for Admin or an owning Business account."""
    conn = get_connection()
    cursor = conn.cursor()
    query = """
    SELECT a.*, j.company_name, j.title, j.business_id, j.tenant_id,
           u.full_name, u.email, u.username
    FROM job_applications a
    JOIN jobs j ON j.id = a.job_id
    JOIN users u ON u.id = a.candidate_id
    """
    params = []
    if business_id:
        query += " WHERE j.business_id = ?"
        params.append(business_id)
    query += " ORDER BY a.applied_at DESC;"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_system_metrics() -> Dict[str, Any]:
    """Retrieve high-level metrics for Admin Dashboard."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users;")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'Candidate';")
    total_candidates = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'Business';")
    total_businesses = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM messages;")
    total_messages = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM resume_analyses;")
    total_resume_analyses = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM mock_interviews;")
    total_interviews = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM documents;")
    total_documents = cursor.fetchone()[0]

    conn.close()

    return {
        "total_users": total_users,
        "candidates": total_candidates,
        "businesses": total_businesses,
        "conversations": total_messages,
        "resume_analyses": total_resume_analyses,
        "mock_interviews": total_interviews,
        "documents": total_documents
    }

def get_dashboard_metrics(user_id: int, role: str, tenant_id: str) -> Dict[str, Any]:
    """Retrieve metrics scoped to the current role, except for the Admin view."""
    if role == "Admin":
        return get_system_metrics()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM conversations WHERE user_id = ?;", (user_id,))
    conversations = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM resume_analyses WHERE user_id = ?;", (user_id,))
    resume_analyses = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM mock_interviews WHERE user_id = ?;", (user_id,))
    mock_interviews = cursor.fetchone()[0]
    cursor.execute(
        "SELECT COUNT(*) FROM documents WHERE tenant_id = ? OR tenant_id = 'tenant_global';",
        (tenant_id,)
    )
    documents = cursor.fetchone()[0]

    if role == "Candidate":
        cursor.execute("SELECT COUNT(*) FROM candidate_profiles WHERE user_id = ?;", (user_id,))
        candidates = cursor.fetchone()[0]
        businesses = 0
    else:
        cursor.execute("SELECT COUNT(*) FROM users WHERE tenant_id = ?;", (tenant_id,))
        candidates = 0
        businesses = cursor.fetchone()[0]

    conn.close()
    return {
        "total_users": 1 if role == "Candidate" else businesses,
        "candidates": candidates,
        "businesses": businesses if role == "Business" else 0,
        "conversations": conversations,
        "resume_analyses": resume_analyses,
        "mock_interviews": mock_interviews,
        "documents": documents
    }
