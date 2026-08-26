import os
import sys
import warnings
import logging


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

import streamlit as st
import pandas as pd
import plotly.express as px
from config import APP_NAME, APP_TAGLINE, get_role_categories, ROLE_CANDIDATE, ROLE_BUSINESS, ROLE_ADMIN, ROLES
from database.database import init_db
from database.models import (
    authenticate_user, create_user, get_all_users, get_system_metrics, get_dashboard_metrics, get_feedback_stats,
    create_conversation, get_user_conversations, get_conversation_messages, save_message,
    record_feedback, get_all_documents, can_delete_document, delete_user, change_password,
    get_unanswered_questions, mark_unanswered_question_resolved
)
from core.rag import rag_pipeline
from core.router import ai_orchestrator
from core.llm import llm_client
from utils.helpers import apply_custom_css, render_header, render_metric_card

# Import Feature Modules
from modules.career import render_career_advisor
from modules.counselling import render_career_counselling
from modules.company_strategy import render_company_strategy
from modules.job_portal import render_admin_job_portal, render_business_job_portal, render_candidate_job_portal
from modules.resume import render_resume_analyzer
from modules.interview import render_mock_interview
from modules.recruitment import render_recruitment
from modules.business import render_business_assistant
from modules.voice import render_voice_assistant

st.set_page_config(
    page_title="Ardhanarishwar — AI SaaS Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_db()

apply_custom_css()

if "user" not in st.session_state:
    st.session_state.user = None
if "current_conversation_id" not in st.session_state:
    st.session_state.current_conversation_id = None

def render_auth_view():
    render_header()
    
    st.markdown("<div style='max-width: 450px; margin: 0 auto;'>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["🔒 User Login", "📝 Register Account"])

    with tab1:
        st.subheader("Login to Ardhanarishwar")
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pwd")
        
        if st.button("Login", type="primary", use_container_width=True):
            user = authenticate_user(username, password)
            if user:
                st.session_state.user = user
                st.success(f"Welcome back, {user['full_name']}!")
                st.rerun()
            else:
                st.error("Invalid username or password.")
        
        st.info("💡 **Demo Credentials**:\n- **Candidate**: `candidate` / `cand123`\n- **Business**: `business` / `biz123`\n- **Admin**: `admin` / `admin123`")

    with tab2:
        st.subheader("Create New Account")
        new_username = st.text_input("Choose Username", key="reg_user")
        new_password = st.text_input("Choose Password", type="password", key="reg_pwd")
        new_name = st.text_input("Full Name", key="reg_name")
        new_email = st.text_input("Email Address", key="reg_email")
        new_role = st.selectbox("Select Role", [ROLE_CANDIDATE, ROLE_BUSINESS])

        if st.button("Register", type="secondary", use_container_width=True):
            if new_username and new_password:
                tenant_id = f"tenant_{new_role.lower()}_{new_username}"
                u_id = create_user(new_username, new_password, new_role, tenant_id, new_email, new_name)
                if u_id:
                    st.success("Account created! Please login.")
                else:
                    st.error("Username already exists.")
            else:
                st.warning("Please fill in required fields.")

    st.markdown("</div>", unsafe_allow_html=True)

if not st.session_state.user:
    render_auth_view()
    st.stop()

user = st.session_state.user
user_role = user['role']

with st.sidebar:
    st.markdown(f"### ⚡ {APP_NAME}")
    st.markdown(f"👤 **{user['full_name']}**")
    st.caption(f"Role: **{user_role}** | Tenant: `{user['tenant_id']}`")
    st.markdown("---")

    # Role-based menu options
    if user_role == ROLE_CANDIDATE:
        nav_options = [
            "Dashboard", "AI Assistant", "Career Advisor", "Career Counselling", "Job Portal", "Resume Analyzer",
            "Mock Interview", "Voice Assistant", "Knowledge Base",
            "Feedback", "Settings"
        ]
    elif user_role == ROLE_BUSINESS:
        nav_options = [
            "Dashboard", "AI Assistant", "Job Portal", "Recruitment Engine", "Business Intelligence",
            "Voice Assistant", "Knowledge Base", "Analytics", "Feedback", "Settings"
        ]
    elif user_role == ROLE_ADMIN:
        nav_options = [
            "Dashboard", "AI Assistant", "Career Advisor", "Company Strategy", "Job Management", "Resume Analyzer",
            "Mock Interview", "Recruitment Engine", "Business Intelligence",
            "Voice Assistant", "Knowledge Base", "Analytics", "Feedback", "User Management", "Settings"
        ]
    else:
        st.error("Your account has an invalid role. Please contact an administrator.")
        st.stop()

    selected_nav = st.radio("Navigation", nav_options)
    st.markdown("---")

    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state.user = None
        st.session_state.current_conversation_id = None
        st.rerun()

if selected_nav == "Dashboard":
    render_header(f"{user_role} Dashboard")
    metrics = get_dashboard_metrics(user['id'], user_role, user['tenant_id'])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Platform Users", metrics['total_users'])
    c2.metric("Candidate Profiles", metrics['candidates'])
    c3.metric("Business Tenants", metrics['businesses'])
    c4.metric("AI Conversations", metrics['conversations'])

    m1, m2, m3 = st.columns(3)
    m1.metric("Resume Analyses", metrics['resume_analyses'])
    m2.metric("Mock Interviews", metrics['mock_interviews'])
    m3.metric("RAG Knowledge Docs", metrics['documents'])

    st.markdown("---")
    st.markdown("### 🚀 Quick Start Actions")
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        st.info("🎯 **Candidate Tools**\nAnalyze your resume ATS score, calculate skill gaps, or start an AI mock interview session.")
    with col_b:
        st.success("💼 **Business Tools**\nExtract job description requirements and batch-rank candidate resumes against job descriptions.")
    with col_c:
        st.warning("📚 **RAG Knowledge Base**\nUpload domain PDF documents into Qdrant for semantic vector search.")


elif selected_nav == "AI Assistant":
    render_header("AI Chat Assistant")

    # Conversation Selector
    user_convs = get_user_conversations(user['id'])
    if not user_convs:
        c_id = create_conversation(user['id'], user['tenant_id'], user_role, "General Chat")
        st.session_state.current_conversation_id = c_id
    elif not st.session_state.current_conversation_id:
        st.session_state.current_conversation_id = user_convs[0]['id']

    c_left, c_right = st.columns([1, 4])
    
    with c_left:
        st.markdown("#### 💬 Conversations")
        if st.button("➕ New Chat", use_container_width=True):
            new_id = create_conversation(user['id'], user['tenant_id'], user_role, f"Chat #{len(user_convs)+1}")
            st.session_state.current_conversation_id = new_id
            st.rerun()

        for conv in user_convs[:8]:
            btn_label = f"💬 {conv['title'][:18]}"
            if st.button(btn_label, key=f"conv_{conv['id']}", use_container_width=True):
                st.session_state.current_conversation_id = conv['id']
                st.rerun()

    with c_right:
        messages = get_conversation_messages(st.session_state.current_conversation_id)
        
        # Display Message History
        for msg in messages:
            with st.chat_message(msg['sender']):
                st.markdown(msg['content'])
                if msg.get('sources'):
                    st.markdown("**📚 Retrieved Sources**:")
                    for s in msg['sources']:
                        st.caption(f"- 📄 {s['document_name']} ({s['category']}) — Match: {s['relevance_score']}%")

        # Chat Input
        prompt = st.chat_input("Ask a career question about Resumes, Skills, Interviews, or Jobs...")
        if prompt:
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Analyzing intent & retrieving knowledge..."):
                    res_text, sources, agent_name = ai_orchestrator.process_request(
                        query=prompt,
                        user_id=user['id'],
                        conversation_id=st.session_state.current_conversation_id,
                        tenant_id=user['tenant_id'],
                        user_role=user_role
                    )
                    st.markdown(res_text)

                    if sources:
                        st.markdown("**📚 Retrieved RAG Context Sources**:")
                        for s in sources:
                            st.caption(f"- 📄 {s['document_name']} ({s['category']}) — Match: {s['relevance_score']}%")

                    # Feedback buttons
                    fb_col1, fb_col2 = st.columns([1, 10])
                    if fb_col1.button("👍", key=f"up_{len(messages)}"):
                        record_feedback(user['id'], prompt, res_text, 1)
                        st.toast("Thank you for positive feedback!")
                    if fb_col2.button("👎", key=f"down_{len(messages)}"):
                        record_feedback(user['id'], prompt, res_text, -1)
                        st.toast("Feedback recorded for continuous model improvement.")

# 3. CAREER ADVISOR & SKILL GAP
elif selected_nav in ["Career Advisor", "Skill Gap"]:
    render_career_advisor(user['id'])

# 3b. CAREER COUNSELLING
elif selected_nav == "Career Counselling":
    render_career_counselling(user['id'], user['tenant_id'])

# 3c. JOB PORTAL
elif selected_nav == "Job Portal":
    if user_role == ROLE_CANDIDATE:
        render_candidate_job_portal(user['id'])
    else:
        render_business_job_portal(user['id'], user['tenant_id'])

# 3d. COMPANY STRATEGY (ADMIN)
elif selected_nav == "Company Strategy":
    render_company_strategy(user['id'], user['tenant_id'])

# 3e. JOB MANAGEMENT (ADMIN)
elif selected_nav == "Job Management":
    render_admin_job_portal()

# 4. RESUME ANALYZER
elif selected_nav == "Resume Analyzer":
    render_resume_analyzer(user['id'])

# 5. MOCK INTERVIEW
elif selected_nav == "Mock Interview":
    render_mock_interview(user['id'])

# 6. RECRUITMENT ENGINE
elif selected_nav == "Recruitment Engine":
    render_recruitment(user['id'])

# 7. BUSINESS INTELLIGENCE
elif selected_nav == "Business Intelligence":
    render_business_assistant(user['id'], user['tenant_id'])

# 8. VOICE ASSISTANT
elif selected_nav == "Voice Assistant":
    render_voice_assistant(user['id'], user['tenant_id'], user_role)

# 9. KNOWLEDGE BASE MANAGEMENT
elif selected_nav == "Knowledge Base":
    render_header("RAG Knowledge Base Manager")
    allowed_categories = get_role_categories(user_role)
    
    st.markdown("### 📚 Upload & Vectorize Documents into Qdrant")
    col_u1, col_u2 = st.columns(2)

    with col_u1:
        kb_file = st.file_uploader("Upload PDF / DOCX / TXT Document", type=["pdf", "docx", "txt"])
        kb_category = st.selectbox("Document Category", allowed_categories)

    with col_u2:
        kb_source = st.text_input("Source / Reference Name", value="Internal Knowledge Base")
        if kb_file and st.button("🚀 Ingest into Qdrant Vector DB", type="primary"):
            with st.spinner("Extracting text, generating embeddings, and storing vectors in Qdrant..."):
                bytes_data = kb_file.read()
                success, msg, chunks = rag_pipeline.ingest_document(
                    file_name=kb_file.name,
                    file_bytes=bytes_data,
                    category=kb_category,
                    source=kb_source,
                    tenant_id="tenant_global" if user_role in [ROLE_ADMIN, ROLE_BUSINESS] else user['tenant_id'],
                    uploaded_by=user['id'],
                    user_role=user_role
                )
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

    st.markdown("---")
    st.markdown("### 📑 Indexed Knowledge Base Documents")
    docs = get_all_documents()
    if docs:
        for doc in docs:
            can_delete = can_delete_document(user, doc)
            col_d1, col_d2, col_d3 = st.columns([3, 2, 1])
            col_d1.write(f"📄 **{doc['document_name']}** ({doc['category']})")
            col_d2.write(f"Chunks: `{doc['chunk_count']}` | Added: {doc['uploaded_at']}")
            if can_delete:
                if col_d3.button("🗑️ Delete", key=f"del_{doc['id']}"):
                    success, msg = rag_pipeline.delete_document(doc['id'], user)
                    if success:
                        st.success(msg)
                    else:
                        st.warning(msg)
                    st.rerun()
            else:
                col_d3.write("🔒")
    else:
        st.info("No documents currently stored in vector database.")

# 10. ANALYTICS (ADMIN / BUSINESS)
elif selected_nav == "Analytics":
    render_header("System & Usage Analytics")
    metrics = get_system_metrics()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Users", metrics['total_users'])
    c2.metric("Candidates", metrics['candidates'])
    c3.metric("Businesses", metrics['businesses'])
    c4.metric("AI Messages", metrics['conversations'])

    # Feedback score analytics
    fb_stats = get_feedback_stats()
    st.markdown("### 📊 Continuous Improvement & Feedback Analytics")
    
    f1, f2, f3 = st.columns(3)
    f1.metric("Total Ratings Received", fb_stats['total_feedback'])
    f2.metric("Positive Satisfaction Rate", f"{fb_stats['positive_pct']}%")
    f3.metric("Negative Satisfaction Rate", f"{fb_stats['negative_pct']}%")

    st.markdown("### 🔔 Candidate Questions Awaiting Knowledge")
    unanswered = get_unanswered_questions()
    if unanswered:
        for item in unanswered:
            col_q, col_action = st.columns([5, 1])
            col_q.write(
                f"**{item['full_name']}** ({item['username']}) | "
                f"{item['created_at']}\n\nQuestion: *{item['question']}*"
            )
            if col_action.button("Resolve", key=f"resolve_question_{item['id']}"):
                mark_unanswered_question_resolved(item['id'])
                st.rerun()
    else:
        st.info("No unanswered candidate questions are pending.")

# 11. FEEDBACK & CONTINUOUS IMPROVEMENT
elif selected_nav == "Feedback":
    render_header("Feedback & Continuous Improvement Loop")
    fb_stats = get_feedback_stats()
    
    st.markdown("### 💬 User Ratings Log")
    if fb_stats['recent_feedback']:
        for fb in fb_stats['recent_feedback']:
            rating_icon = "👍 Helpful" if fb['rating'] == 1 else "👎 Not Helpful"
            st.write(f"**{rating_icon}** | Question: *\"{fb['question']}\"* | {fb['created_at']}")
    else:
        st.info("No user feedback submitted yet.")

# 12. USER MANAGEMENT (ADMIN ONLY)
elif selected_nav == "User Management":
    render_header("Admin User Management")
    users_list = get_all_users()
    for managed_user in users_list:
        col_u1, col_u2 = st.columns([5, 1])
        col_u1.write(f"**{managed_user['full_name']}** | {managed_user['username']} | {managed_user['role']} | `{managed_user['tenant_id']}`")
        if managed_user['id'] != user['id'] and col_u2.button("Delete", key=f"delete_user_{managed_user['id']}"):
            if delete_user(user, managed_user['id']):
                st.success("User deleted successfully.")
                st.rerun()
            else:
                st.error("User could not be deleted.")

# 13. SETTINGS
elif selected_nav == "Settings":
    render_header("System Settings")

    st.markdown("### 🔐 Change Your Password")
    with st.form("change_password_form"):
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        change_password_submitted = st.form_submit_button("Update Password", type="primary")

    if change_password_submitted:
        if not current_password or not new_password or not confirm_password:
            st.warning("Please fill in all password fields.")
        elif len(new_password) < 8:
            st.warning("New password must be at least 8 characters long.")
        elif new_password != confirm_password:
            st.error("New password and confirmation do not match.")
        elif change_password(user['id'], current_password, new_password):
            st.success("Password changed successfully. Use the new password next time you log in.")
        else:
            st.error("Current password is incorrect.")

    st.markdown("---")
    
    st.markdown("### ⚙️ Ollama Local LLM Connection Status")
    available = llm_client.check_availability()
    if available:
        st.success(f"🟢 Ollama is ACTIVE on `http://localhost:11434` (Default Model: `{llm_client.model}`)")
        models = llm_client.list_available_models()
        st.write("Pulled Local Models:", models)
    else:
        st.warning("⚠️ Ollama service is currently not detected on `http://localhost:11434`. Local fallback responses active.")
        st.info("To run Ollama locally:\n1. Download from `https://ollama.com`\n2. Open terminal and run `ollama serve`\n3. Run `ollama pull llama3.2`")
