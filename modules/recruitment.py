import streamlit as st
import pandas as pd
from utils.pdf import extract_text_from_file, parse_resume_structure
from utils.scoring import match_resume_to_jd
from core.llm import llm_client
from utils.helpers import render_header

def render_recruitment(user_id: int):
    """Render Business Recruitment & Candidate Batch Matching Engine."""
    render_header("Recruitment & Candidate Matcher Engine")

    tabs = st.tabs(["📝 Job Description Analyzer", "👥 Candidate Matcher Engine", "❓ Interview Question Generator"])

    # TAB 1: JOB DESCRIPTION ANALYZER
    with tabs[0]:
        st.markdown("### 📋 Analyze & Extract Job Description Requirements")
        
        jd_input = st.text_area(
            "Paste Job Description Text or Upload File Below",
            height=200,
            value="""Senior AI Engineer - TechCorp
Experience: 3-5 Years
Required Skills: Python, RAG, Ollama, Qdrant, FastAPI, Docker, SQL, Git
Preferred Skills: Kubernetes, PyTorch, System Design
Responsibilities:
- Build and maintain local Retrieval-Augmented Generation (RAG) pipelines.
- Integrate vector search databases with open-source LLMs.
- Implement robust microservices using FastAPI and Docker."""
        )

        if st.button("🔍 Extract Requirements (Local LLM)", type="primary"):
            with st.spinner("Extracting structured skills and responsibilities..."):
                prompt = f"Extract structured details (Job Title, Experience Level, Required Skills, Preferred Skills, Core Responsibilities) from this Job Description:\n{jd_input}"
                extracted_res = llm_client.generate(prompt)
                st.markdown(extracted_res)
                st.session_state.active_jd_text = jd_input

    # TAB 2: CANDIDATE MATCHING ENGINE (MAIN BUSINESS FEATURE)
    with tabs[1]:
        st.markdown("### 🎯 Batch Candidate Resume Ranking Engine")
        st.info("Upload multiple candidate resumes to compare and rank them against the active Job Description.")

        jd_for_match = st.text_area(
            "Active Target Job Description",
            value=st.session_state.get("active_jd_text", "Senior AI Engineer. Required: Python, RAG, Vector DB, Qdrant, FastAPI, Docker, SQL."),
            height=120
        )

        uploaded_resumes = st.file_uploader(
            "Upload Candidate Resumes (PDF, DOCX, TXT)",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True,
            key="batch_resumes"
        )

        if uploaded_resumes and st.button("🚀 Run Candidate Matching & Ranking", type="primary"):
            with st.spinner("Evaluating candidate resumes against Job Description..."):
                candidate_results = []

                for file in uploaded_resumes:
                    b_data = file.read()
                    text = extract_text_from_file(file.name, b_data)
                    parsed = parse_resume_structure(text)
                    match_res = match_resume_to_jd(parsed['skills'], text, jd_for_match)

                    candidate_results.append({
                        "Candidate Name": parsed['candidate_name'],
                        "Resume File": file.name,
                        "Match Score (%)": match_res['match_score'],
                        "Recommendation": match_res['recommendation_badge'],
                        "Matching Skills": ", ".join(match_res['matching_skills']) if match_res['matching_skills'] else "None",
                        "Missing Skills": ", ".join(match_res['missing_skills']) if match_res['missing_skills'] else "None",
                        "Raw Score": match_res['match_score']
                    })

                # Sort candidates by Match Score descending
                candidate_results.sort(key=lambda x: x['Raw Score'], reverse=True)

                st.markdown("---")
                st.markdown("### 🏆 Candidate Match Ranking Leaderboard")

                df = pd.DataFrame(candidate_results)
                st.dataframe(
                    df[["Candidate Name", "Resume File", "Match Score (%)", "Recommendation", "Matching Skills", "Missing Skills"]],
                    use_container_width=True
                )

                st.markdown("#### 🌟 Candidate Profiles Breakdown")
                for c in candidate_results:
                    with st.expander(f"{c['Recommendation']} | {c['Candidate Name']} — Match: {c['Match Score (%)']}%"):
                        st.write(f"**Resume File**: {c['Resume File']}")
                        st.write(f"**Matching Skills**: {c['Matching Skills']}")
                        st.write(f"**Missing Skills**: {c['Missing Skills']}")
                        if c['Raw Score'] >= 80:
                            st.success("Strong Candidate: Highly recommended for interview screening.")
                        elif c['Raw Score'] >= 60:
                            st.warning("Moderate Candidate: Relevant background, check missing skills.")
                        else:
                            st.error("Weak Candidate: Significant skill gap for this specific role.")

    # TAB 3: INTERVIEW QUESTION GENERATOR
    with tabs[2]:
        st.markdown("### ❓ Custom AI Interview Question Generator")
        
        target_role_q = st.text_input("Target Role", value="Python AI Engineer")
        categories_q = st.multiselect("Question Domains", ["Python", "Machine Learning", "RAG", "LLM", "APIs", "System Design"], default=["Python", "RAG", "LLM", "System Design"])

        if st.button("⚡ Generate Domain Categorized Questions", type="secondary"):
            with st.spinner("Generating question bank with Ollama..."):
                domains_str = ", ".join(categories_q)
                prompt = f"Generate 2 technical interview questions for each of these domains ({domains_str}) for a {target_role_q} candidate."
                q_bank = llm_client.generate(prompt)
                st.markdown(q_bank)
