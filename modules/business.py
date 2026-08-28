import streamlit as st
from core.router import ai_orchestrator
from utils.helpers import render_header

def render_business_assistant(user_id: int, tenant_id: str):
    """Render Business & Workforce Intelligence Assistant."""
    render_header("Business & HR Intelligence Assistant")

    st.markdown("### 💼 Ask Business, Recruitment & HR Queries")
    st.info("Leverages local open-source LLM and RAG Knowledge Base for company business intelligence.")

    # Preset Quick Action Buttons
    st.markdown("#### ⚡ Quick Business Actions")
    q_col1, q_col2, q_col3 = st.columns(3)

    query_preset = ""
    if q_col1.button("📋 Draft AI Team Hiring Plan"):
        query_preset = "Create a structured 3-month hiring plan for a 5-member AI Engineering team including roles, skill requirements, and budget strategy."
    if q_col2.button("🔍 Candidate Screening Checklist"):
        query_preset = "Provide an HR candidate screening checklist and scoring rubric for evaluating Senior Developers."
    if q_col3.button("📊 Workforce Optimization Strategy"):
        query_preset = "How can a mid-sized tech company optimize workforce productivity using local open-source AI tools?"

    user_query = st.text_area("Your Business Question:", value=query_preset, height=120, placeholder="e.g. How to structure our engineering hiring pipeline for 2026?")

    if st.button("🚀 Submit Business Query", type="primary"):
        if not user_query.strip():
            st.warning("Please type a business question.")
        else:
            with st.spinner("Processing request with Business Agent & Qdrant RAG..."):
                response, sources, agent_name = ai_orchestrator.process_request(
                    query=user_query,
                    user_id=user_id,
                    category_filter="Business",
                    tenant_id=tenant_id,
                    user_role="Business"
                )

                st.markdown(f"### 🤖 Response from **{agent_name}**")
                st.markdown(response)

                if sources:
                    st.markdown("---")
                    st.markdown("#### 📚 Retrieved RAG Knowledge Sources")
                    for src in sources:
                        st.write(f"📄 **{src['document_name']}** ({src['category']}) - Relevance: **{src['relevance_score']}%**")
                        st.caption(f"Snippet: {src['snippet']}")
