import streamlit as st
from core.llm import llm_client
from utils.helpers import render_header


def render_career_counselling(user_id: int):
    """Render education and career-path counselling for candidates."""
    render_header("Career Counselling Studio")

    st.markdown("### 🎓 Find Your Education & Career Direction")
    st.info(
        "Build a counselling profile to compare suitable colleges, courses, "
        "private or government job paths, and your next steps."
    )

    with st.form("career_counselling_form"):
        col1, col2 = st.columns(2)
        with col1:
            education_level = st.selectbox(
                "Current Education",
                ["Class 10", "Class 12", "Diploma", "Undergraduate", "Postgraduate", "Working Professional"]
            )
            stream = st.selectbox(
                "Stream or Field",
                ["Science", "Commerce", "Arts/Humanities", "Engineering/Technology", "Medical/Healthcare", "Other"]
            )
            interests = st.text_input(
                "Interests and Strong Subjects",
                placeholder="e.g. mathematics, coding, design, public service"
            )
            academic_score = st.text_input(
                "Marks, CGPA, or Entrance Rank",
                placeholder="e.g. 82%, 8.1 CGPA, or not yet available"
            )

        with col2:
            preferred_path = st.selectbox(
                "Preferred Job Direction",
                ["Not sure yet", "Private sector", "Government sector", "Both private and government"]
            )
            location = st.text_input(
                "Preferred Study or Job Location",
                placeholder="e.g. Delhi, Bengaluru, or anywhere in India"
            )
            college_budget = st.selectbox(
                "College Budget Preference",
                ["Need scholarship or low-cost options", "Moderate budget", "Open to premium colleges"]
            )
            budget_amount = st.text_input(
                "Maximum Annual College Budget",
                placeholder="e.g. Rs. 1 lakh per year"
            )

        additional_context = st.text_area(
            "Goals, Family Priorities, or Constraints",
            placeholder="Mention entrance exams, relocation limits, family priorities, or your long-term goal.",
            height=100
        )
        submitted = st.form_submit_button("🔍 Get Counselling Recommendation", type="primary")

    if submitted:
        if not interests.strip() and not additional_context.strip():
            st.warning("Please add at least your interests or one goal so the recommendation can be personal.")
        else:
            counselling_query = (
                f"Career counselling for a {education_level} student in {stream}. "
                f"Interests: {interests}. Academic score: {academic_score}. "
                f"Preferred direction: {preferred_path}. Location: {location}. "
                f"Budget preference: {college_budget}. Maximum annual budget: {budget_amount}. "
                f"Additional context: {additional_context}"
            )

            with st.spinner("Preparing your counselling recommendation with Ollama..."):
                prompt = f"""
Create a practical career counselling recommendation using the candidate details below.

Education level: {education_level}
Stream or field: {stream}
Interests: {interests}
Academic score or entrance rank: {academic_score}
Preferred job direction: {preferred_path}
Location: {location}
College budget: {college_budget}
Maximum annual budget: {budget_amount}
Additional context: {additional_context}

Cover:
1. Suggest suitable course or career-path types based on the candidate's interests and background.
2. Provide a checklist to compare colleges, including accreditation, curriculum, eligibility, fees, scholarships, location, and verified placement data.
3. Suggest suitable private-sector and government-sector job paths based on the answers.
4. Give a 30-day action plan and relevant exams or skills to research.
5. Clearly distinguish general guidance from facts that must be verified with official sources.

Do not invent or rank specific colleges, fees, eligibility rules, admission dates, placement rates, or guaranteed salaries. Direct the candidate to official college and exam websites for current information.
"""
                response = llm_client.generate(
                    prompt,
                    system_prompt=(
                        "You are a Senior career counsellor. Give balanced, actionable guidance "
                        "and distinguish general advice from facts that require official verification."
                    )
                )

            st.markdown("### 🧭 Your Counselling Recommendation")
            st.markdown(response)
