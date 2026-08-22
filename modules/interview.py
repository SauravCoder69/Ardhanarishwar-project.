import streamlit as st
from database.models import save_mock_interview, get_user_interviews
from core.llm import llm_client
from utils.helpers import render_header

def render_mock_interview(user_id: int):
    """Render Interactive AI Mock Interview Assistant."""
    render_header("AI Mock Interview Assistant")

    if "interview_active" not in st.session_state:
        st.session_state.interview_active = False
        st.session_state.current_q_index = 0
        st.session_state.interview_q_list = []
        st.session_state.user_answers = []
        st.session_state.evaluations = []

    # Interview Configuration
    if not st.session_state.interview_active:
        st.markdown("### 🎯 Configure Your Mock Interview Session")
        
        col1, col2 = st.columns(2)
        with col1:
            job_role = st.selectbox("Target Job Role", ["AI Developer", "ML Engineer", "Python Developer", "Data Scientist", "Software Developer"])
            experience_level = st.selectbox("Experience Level", ["Junior (0-2 Yrs)", "Mid (2-5 Yrs)", "Senior (5+ Yrs)"])
        
        with col2:
            difficulty = st.selectbox("Difficulty Level", ["Easy", "Medium", "Hard"])
            interview_type = st.selectbox("Interview Focus Type", ["Technical & Coding", "System Design & RAG", "Behavioral & HR"])

        if st.button("🚀 Start Interactive Mock Interview", type="primary"):
            st.session_state.job_role = job_role
            st.session_state.experience_level = experience_level
            st.session_state.difficulty = difficulty
            st.session_state.interview_type = interview_type

            # Generate Questions via Ollama LLM
            with st.spinner("Generating targeted technical interview questions..."):
                prompt = f"""
Generate exactly 3 structured {difficulty} interview questions for a {experience_level} {job_role} candidate focusing on {interview_type}.
Output only the 3 numbered questions.
"""
                raw_q = llm_client.generate(prompt)
                lines = [line.strip() for line in raw_q.split('\n') if line.strip() and (line[0].isdigit() or line.startswith('-'))]
                if len(lines) < 3:
                    lines = [
                        f"1. Explain the fundamental architecture of a RAG pipeline and vector search in {job_role}.",
                        f"2. How do you handle asynchronous request execution and performance optimization in Python?",
                        f"3. Describe a challenging engineering bottleneck you solved and how you validated the resolution."
                    ]
                
                st.session_state.interview_q_list = lines[:3]
                st.session_state.interview_active = True
                st.session_state.current_q_index = 0
                st.session_state.user_answers = []
                st.session_state.evaluations = []
                st.rerun()

        # Display Previous Interview History
        st.markdown("---")
        st.markdown("### 📜 Past Interview Sessions")
        history = get_user_interviews(user_id)
        if history:
            for item in history[:5]:
                st.write(f"📅 **{item['created_at']}** | Role: **{item['job_role']}** | Difficulty: {item['difficulty']} | Overall Score: **{item['score_overall']}/100**")
        else:
            st.info("No past interview sessions recorded yet.")

    else:
        # ACTIVE INTERVIEW INTERFACE
        q_idx = st.session_state.current_q_index
        total_q = len(st.session_state.interview_q_list)

        if q_idx < total_q:
            st.markdown(f"### Question {q_idx + 1} of {total_q}")
            st.progress((q_idx + 1) / total_q)
            
            question_text = st.session_state.interview_q_list[q_idx]
            st.info(f"🎤 **Interviewer**: {question_text}")

            answer_input = st.text_area("Your Response / Code Explanation:", height=150, key=f"ans_{q_idx}")

            if st.button("Submit Answer & Next Question ➔", type="primary"):
                if not answer_input.strip():
                    st.warning("Please type your response before submitting.")
                else:
                    # Evaluate single answer via LLM
                    with st.spinner("Evaluating your response..."):
                        eval_prompt = f"""
Question: {question_text}
Candidate Answer: {answer_input}

Evaluate the candidate's answer on a scale of 0-100 for:
1. Technical Accuracy
2. Relevance & Clarity
3. Communication Quality

Return a short 3-bullet evaluation summary with score out of 100.
"""
                        eval_res = llm_client.generate(eval_prompt)
                        
                        # Compute dynamic scores based on response quality and keywords
                        words = len(answer_input.split())
                        comm = min(98.0, max(30.0, 50.0 + (words * 0.7)))
                        tech_kws = ["rag", "vector", "embedding", "python", "ollama", "qdrant", "sql", "api", "fastapi", "docker", "async", "cache", "model", "llm", "context", "system", "database"]
                        tech_hits = sum(1 for kw in tech_kws if kw in answer_input.lower())
                        tech = min(98.0, max(25.0, 45.0 + (tech_hits * 10.0)))
                        
                        if any(w in eval_res.lower() for w in ["good", "accurate", "correct", "strong", "excellent"]):
                            tech = min(99.0, tech + 10.0)
                            comm = min(99.0, comm + 5.0)
                        elif any(w in eval_res.lower() for w in ["incorrect", "wrong", "poor", "lacks", "missing"]):
                            tech = max(20.0, tech - 20.0)

                        overall = round((tech * 0.6) + (comm * 0.4), 1)

                        if "question_scores" not in st.session_state:
                            st.session_state.question_scores = []
                        st.session_state.question_scores.append((overall, round(tech, 1), round(comm, 1)))

                        st.session_state.user_answers.append(answer_input)
                        st.session_state.evaluations.append(eval_res)
                        st.session_state.current_q_index += 1
                        st.rerun()
        else:
            # INTERVIEW SUMMARY REPORT
            st.markdown("### 🏆 Interview Performance Summary Report")
            
            q_scores = st.session_state.get("question_scores", [(80.0, 80.0, 80.0)])
            overall_score = round(sum(s[0] for s in q_scores) / len(q_scores), 1)
            tech_score = round(sum(s[1] for s in q_scores) / len(q_scores), 1)
            comm_score = round(sum(s[2] for s in q_scores) / len(q_scores), 1)

            c1, c2, c3 = st.columns(3)
            c1.metric("Overall Score", f"{overall_score}/100")
            c2.metric("Technical Score", f"{tech_score}/100")
            c3.metric("Communication Score", f"{comm_score}/100")

            st.markdown("---")
            st.markdown("#### 📝 Detailed Question Breakdown & Feedback")

            for i in range(total_q):
                st.markdown(f"**Q{i+1}: {st.session_state.interview_q_list[i]}**")
                st.markdown(f"*Your Answer*: {st.session_state.user_answers[i]}")
                st.markdown(f"*AI Evaluation*:\n{st.session_state.evaluations[i]}")
                st.markdown("---")

            # Save interview to DB
            save_mock_interview(
                user_id=user_id,
                job_role=st.session_state.job_role,
                experience_level=st.session_state.experience_level,
                difficulty=st.session_state.difficulty,
                interview_type=st.session_state.interview_type,
                score_overall=overall_score,
                score_technical=tech_score,
                score_communication=comm_score,
                summary_feedback=f"Candidate achieved overall technical score of {tech_score}% and communication score of {comm_score}%."
            )

            if st.button("🔄 Start New Interview Session"):
                st.session_state.interview_active = False
                st.rerun()
