import streamlit as st
from utils.pdf import extract_text_from_file, parse_resume_structure
from utils.scoring import calculate_ats_score, match_resume_to_jd
from database.models import save_resume_analysis
from core.llm import llm_client
from utils.helpers import render_header

def render_resume_analyzer(user_id: int):
    """Render Candidate Resume Analyzer & Job Description Compatibility Engine."""
    render_header("Resume Analyzer & JD Matcher")

    tabs = st.tabs(["📄 Resume ATS Analyzer", "🎯 Resume ↔ JD Matcher"])

    # TAB 1: RESUME ATS ANALYZER
    with tabs[0]:
        st.markdown("### Upload Resume for ATS Quality Check")
        uploaded_file = st.file_uploader("Choose Resume PDF, DOCX or TXT", type=["pdf", "docx", "txt"], key="cand_resume")

        if uploaded_file:
            bytes_data = uploaded_file.read()
            raw_text = extract_text_from_file(uploaded_file.name, bytes_data)
            
            if not raw_text or len(raw_text.strip()) < 20:
                st.error("Could not extract text from uploaded file. Please ensure it is not an image-only scan.")
            else:
                parsed = parse_resume_structure(raw_text)
                ats = calculate_ats_score(raw_text, parsed['skills'])

                st.success(f"Successfully processed **{uploaded_file.name}**")

                col1, col2, col3 = st.columns(3)
                col1.metric("ATS Quality Score", f"{ats['ats_score']}%")
                col2.metric("Detected Skills", len(parsed['skills']))
                col3.metric("Word Count", ats['word_count'])

                st.markdown("---")
                c_left, c_right = st.columns(2)

                with c_left:
                    st.markdown("#### 👤 Extracted Candidate Details")
                    st.write(f"**Name**: {parsed['candidate_name']}")
                    st.write(f"**Email**: {parsed['email']}")
                    st.write(f"**Phone**: {parsed['phone']}")
                    st.write(f"**Education**: {parsed['education']}")
                    st.markdown("**Detected Technical Skills**:")
                    st.info(", ".join(parsed['skills']) if parsed['skills'] else "No standard skills detected.")

                with c_right:
                    st.markdown("#### 🎯 ATS Evaluation Summary")
                    st.markdown("**Strengths**:")
                    for s in ats['strengths']:
                        st.markdown(f"- ✅ {s}")

                    st.markdown("**Areas for Improvement**:")
                    for w in ats['weaknesses']:
                        st.markdown(f"- ⚠️ {w}")

                st.markdown("---")
                st.markdown("#### 💡 Formatting & Content Improvement Suggestions")
                for item in ats['formatting_suggestions']:
                    st.markdown(f"- 📌 {item}")

                st.markdown("#### 📝 Sample Bullet Point Enhancements")
                for bullet in ats['bullet_point_improvements']:
                    st.markdown(f"> {bullet}")

                if st.button("🤖 Generate AI Bullet Point Rewrites (Local LLM)", type="secondary"):
                    with st.spinner("Analyzing resume content with Ollama..."):
                        prompt = f"Resume Content:\n{raw_text[:1500]}\n\nProvide 3 high-impact resume bullet point revisions focusing on technical metrics and quantifiable achievements."
                        llm_out = llm_client.generate(prompt)
                        st.markdown(llm_out)

                # Save record to DB
                save_resume_analysis(
                    user_id=user_id,
                    resume_name=uploaded_file.name,
                    ats_score=ats['ats_score'],
                    target_job="General",
                    match_score=0.0,
                    extracted_skills=", ".join(parsed['skills'])
                )

    # TAB 2: RESUME ↔ JD MATCHING
    with tabs[1]:
        st.markdown("### Job Description Compatibility Matcher")
        
        col_jd1, col_jd2 = st.columns(2)

        with col_jd1:
            resume_text_input = st.text_area("Paste Resume Text or Skills", height=200, placeholder="Paste your resume text here...")
        
        with col_jd2:
            jd_text_input = st.text_area("Paste Job Description (JD)", height=200, placeholder="Paste target Job Description here...")

        if st.button("🔍 Calculate JD Compatibility Score", type="primary"):
            if not resume_text_input.strip() or not jd_text_input.strip():
                st.warning("Please provide both Resume Text and Job Description to calculate match score.")
            else:
                parsed_res = parse_resume_structure(resume_text_input)
                match_res = match_resume_to_jd(parsed_res['skills'], resume_text_input, jd_text_input)

                st.markdown("---")
                m1, m2, m3 = st.columns(3)
                m1.metric("Compatibility Match", f"{match_res['match_score']}%")
                m2.metric("Recommendation", match_res['recommendation'])
                m3.metric("Skill Overlap", f"{match_res['skill_match_percentage']}%")

                st.markdown(f"### Assessment Status: {match_res['recommendation_badge']}")

                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.markdown("#### 🟢 Matching Skills Found in Resume")
                    if match_res['matching_skills']:
                        for sk in match_res['matching_skills']:
                            st.markdown(f"- ✅ **{sk}**")
                    else:
                        st.write("No direct skill matches detected.")

                with col_m2:
                    st.markdown("#### 🔴 Missing Skills Required by JD")
                    if match_res['missing_skills']:
                        for sk in match_res['missing_skills']:
                            st.markdown(f"- ⚠️ **{sk}**")
                    else:
                        st.write("No missing skills! Candidate satisfies all JD key skills.")

                ats_res = calculate_ats_score(resume_text_input, parsed_res['skills'])

                # Save record to DB
                save_resume_analysis(
                    user_id=user_id,
                    resume_name="Custom JD Comparison",
                    ats_score=ats_res['ats_score'],
                    target_job="JD Match Job",
                    match_score=match_res['match_score'],
                    extracted_skills=", ".join(match_res['matching_skills'])
                )
