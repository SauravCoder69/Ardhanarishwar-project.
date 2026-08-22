import streamlit as st
import plotly.express as px
import pandas as pd
from database.models import get_candidate_profile, save_candidate_profile
from utils.scoring import analyze_skill_gap
from core.llm import llm_client
from utils.helpers import render_header

def render_career_advisor(user_id: int):
    """Render Candidate Career Advisor & Skill Gap Visualizer."""
    render_header("Career Advisor & Skill Gap Analysis")

    profile = get_candidate_profile(user_id)

    st.markdown("### 📋 Candidate Profile & Career Aspirations")
    col1, col2 = st.columns(2)

    with col1:
        education = st.text_input("Education Background", value=profile.get('education', 'B.Tech Computer Science'))
        current_skills_input = st.text_area("Current Technical Skills (comma separated)", value=profile.get('current_skills', 'Python, SQL, HTML, CSS, Git, Machine Learning'))
        experience = st.text_input("Years of Experience", value=profile.get('experience', '2 Years'))

    with col2:
        career_goal = st.selectbox(
            "Target Career Goal / Role",
            ["AI Engineer", "ML Engineer", "Python Developer", "Data Scientist", "Full Stack Developer"],
            index=0
        )
        preferred_role = st.text_input("Preferred Role Title", value=profile.get('preferred_role', 'Senior AI Engineer'))
        learning_interests = st.text_input("Learning Interests", value=profile.get('learning_interests', 'RAG, Vector DBs, Ollama, Docker, Cloud Deployment'))

    if st.button("💾 Save Profile & Generate Roadmap", type="primary"):
        save_candidate_profile(user_id, education, current_skills_input, experience, career_goal, preferred_role, learning_interests)
        st.success("Profile saved successfully! Generating personalized skill gap report...")

    st.markdown("---")

    # Perform Skill Gap Analysis
    skills_list = [s.strip() for s in current_skills_input.split(",") if s.strip()]
    gap_result = analyze_skill_gap(skills_list, career_goal)

    # Visual Skill Breakdown
    st.markdown(f"### 📊 Skill Coverage for **{career_goal}**")

    c1, c2, c3 = st.columns(3)
    c1.metric("Matching Skills", len(gap_result['matching_skills']))
    c2.metric("Missing Skills", len(gap_result['missing_skills']))
    c3.metric("Goal Readiness", f"{gap_result['completion_percentage']}%")

    st.progress(gap_result['completion_percentage'] / 100.0)

    # Donut Chart Visualization
    chart_data = pd.DataFrame({
        "Status": ["Matching Skills", "Missing Skills"],
        "Count": [len(gap_result['matching_skills']), len(gap_result['missing_skills'])]
    })
    fig = px.pie(
        chart_data,
        names="Status",
        values="Count",
        hole=0.5,
        color="Status",
        color_discrete_map={"Matching Skills": "#22c55e", "Missing Skills": "#ef4444"},
        title="Skill Gap Overview"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Roadmap Steps Display
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### ✅ Skills You Have")
        for sk in gap_result['matching_skills']:
            st.markdown(f"- 🟢 **{sk}**")

    with col_right:
        st.markdown("#### 🚀 Target Skills to Learn")
        for sk in gap_result['missing_skills']:
            st.markdown(f"- 🔴 **{sk}**")

    st.markdown("---")
    st.markdown("### 🗺️ AI-Generated Personal Learning & Project Roadmap")

    if st.button("🤖 Generate Detailed AI Roadmap (Local LLM)", type="secondary"):
        with st.spinner("Analyzing candidate profile with Ollama local LLM..."):
            prompt = f"""
Candidate Goal: {career_goal}
Current Skills: {current_skills_input}
Experience: {experience}
Missing Skills identified: {', '.join(gap_result['missing_skills'])}

Generate a structured 6-step roadmap including:
1. Short-term priorities (Month 1-2)
2. Mid-term priorities (Month 3-4)
3. 2 Practical Project ideas to build
4. Suggested open-source tools & technologies
5. Interview prep recommendation
"""
            llm_response = llm_client.generate(prompt)
            st.markdown(llm_response)
