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
from config import APP_NAME, ROLE_CANDIDATE, ROLE_ADMIN
from database.database import init_db
from database.models import (
    authenticate_user, create_user, get_all_users, get_system_metrics, get_dashboard_metrics,
    get_feedback_stats, delete_user, change_password,
)
from core.llm import llm_client
from utils.helpers import apply_custom_css, render_header

from modules.career import render_career_advisor
from modules.career_chat import render_career_chat
from modules.job_aggregator import render_job_search, render_my_applications
from modules.job_portal import render_admin_job_portal
from modules.resume import render_resume_analyzer
from modules.interview import render_mock_interview

st.set_page_config(
    page_title="Ardhanarishwar — AI Job Aggregator & Career Assistant",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_db()

apply_custom_css()

if "user" not in st.session_state:
    st.session_state.user = None
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
        
    with tab2:
        st.subheader("Create New Account")
        new_username = st.text_input("Choose Username", key="reg_user")
        new_password = st.text_input("Choose Password", type="password", key="reg_pwd")
        new_name = st.text_input("Full Name", key="reg_name")
        new_email = st.text_input("Email Address", key="reg_email")
        if st.button("Register", type="secondary", use_container_width=True):
            if new_username and new_password:
                if len(new_password) < 8:
                    st.error("Password must be at least 8 characters long.")
                    st.stop()
                tenant_id = f"tenant_candidate_{new_username}"
                u_id = create_user(new_username, new_password, ROLE_CANDIDATE, tenant_id, new_email, new_name)
                if u_id:
                    st.success("Account created! Please login.")
                else:
                    st.error("Username already exists.")
            else:
                st.warning("Please fill in required fields.")

    st.markdown("</div>", unsafe_allow_html=True)

def render_password_change(current_user):
    st.markdown("### 🔐 Change Your Password")
    with st.form(f"change_password_form_{current_user['id']}"):
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        submitted = st.form_submit_button("Update Password", type="primary")

    if submitted:
        if not current_password or not new_password or not confirm_password:
            st.warning("Please fill in all password fields.")
        elif len(new_password) < 8:
            st.warning("New password must be at least 8 characters long.")
        elif new_password != confirm_password:
            st.error("New password and confirmation do not match.")
        elif change_password(current_user["id"], current_password, new_password):
            st.success("Password changed successfully.")
        else:
            st.error("Current password is incorrect.")

if not st.session_state.user:
    render_auth_view()
    st.stop()

user = st.session_state.user
user_role = user['role']

if user_role not in (ROLE_CANDIDATE, ROLE_ADMIN):
    st.warning("Business workspaces are no longer available. Existing account data has been retained.")
    if st.button("Sign out"):
        st.session_state.user = None
        st.rerun()
    st.stop()

with st.sidebar:
    st.markdown(f"### ⚡ {APP_NAME}")
    st.markdown(f"👤 **{user['full_name']}**")
    st.caption(f"Role: **{user_role}**")
    st.markdown("---")

    if user_role == ROLE_CANDIDATE:
        nav_options = ["Dashboard", "Find Jobs", "My Applications", "My Profile"]
    else:
        nav_options = ["Dashboard", "Job Management", "Analytics", "User Management", "Settings"]

    selected_nav = st.radio("Navigation", nav_options)
    st.markdown("---")

    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state.user = None
        st.rerun()

if selected_nav == "Dashboard":
    if user_role == ROLE_ADMIN:
        render_header("Admin Dashboard")
        metrics = get_system_metrics(user)
        c1, c2, c3 = st.columns(3)
        c1.metric("Users", metrics["total_users"])
        c2.metric("Candidates", metrics["candidates"])
        c3.metric("AI Messages", metrics["conversations"])
        st.caption("Account, application, and knowledge administration is available in the Admin navigation.")
    else:
        render_header("Candidate Dashboard")
        metrics = get_dashboard_metrics(user["id"], user_role, user["tenant_id"], user)
        c1, c2, c3 = st.columns(3)
        c1.metric("Resume analyses", metrics["resume_analyses"])
        c2.metric("Mock interviews", metrics["mock_interviews"])
        c3.metric("Career conversations", metrics["conversations"])
        st.info("Find Jobs searches current listings. My Applications tracks saved roles. My Profile contains your career tools.")

elif selected_nav == "Find Jobs":
    render_job_search(user)

elif selected_nav == "My Applications":
    render_my_applications(user)

elif selected_nav == "My Profile":
    render_header("My Profile & Career Tools")
    profile_tabs = st.tabs(["Career assistant", "Career guidance", "Resume & ATS", "Interview practice", "Account security"])
    with profile_tabs[0]:
        render_career_chat(user)
    with profile_tabs[1]:
        render_career_advisor(user["id"])
    with profile_tabs[2]:
        render_resume_analyzer(user["id"])
    with profile_tabs[3]:
        render_mock_interview(user["id"])
    with profile_tabs[4]:
        render_password_change(user)

elif selected_nav == "Job Management" and user_role == ROLE_ADMIN:
    render_admin_job_portal(user)

# Admin-only analytics
elif selected_nav == "Analytics" and user_role == ROLE_ADMIN:
    render_header("System & Usage Analytics")
    metrics = get_system_metrics(user)

    c1, c2, c3 = st.columns(3)
    c1.metric("Users", metrics['total_users'])
    c2.metric("Candidates", metrics['candidates'])
    c3.metric("AI Messages", metrics['conversations'])

    # Feedback score analytics
    fb_stats = get_feedback_stats(user)
    st.markdown("### 📊 Continuous Improvement & Feedback Analytics")
    
    f1, f2, f3 = st.columns(3)
    f1.metric("Total Ratings Received", fb_stats['total_feedback'])
    f2.metric("Positive Satisfaction Rate", f"{fb_stats['positive_pct']}%")
    f3.metric("Negative Satisfaction Rate", f"{fb_stats['negative_pct']}%")

# User management is available only in the Admin navigation.
elif selected_nav == "User Management" and user_role == ROLE_ADMIN:
    render_header("Admin User Management")
    users_list = get_all_users(user)
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

    render_password_change(user)

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
