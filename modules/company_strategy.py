import streamlit as st
from core.llm import llm_client
from core.rag import rag_pipeline
from utils.helpers import render_header


def render_company_strategy(user_id: int, tenant_id: str):
    """Render Admin company growth, finance, and crisis-planning assistant."""
    render_header("Company Strategy & Financial Health")

    st.markdown("### 🏢 Analyze Your Company")
    st.info(
        "Describe your company and current challenge to get a practical plan for growth, "
        "financial control, crisis recovery, and low-budget operations."
    )

    col1, col2 = st.columns(2)
    with col1:
        company_type = st.text_input("Company or Industry", placeholder="e.g. SaaS startup, retail, manufacturing")
        company_stage = st.selectbox(
            "Company Stage",
            ["Idea/Pre-revenue", "Early startup", "Growing SME", "Established company", "Under financial stress"]
        )
        team_size = st.number_input("Team Size", min_value=1, value=10, step=1)
        monthly_revenue = st.text_input("Approximate Monthly Revenue", placeholder="e.g. Rs. 5 lakh or pre-revenue")

    with col2:
        monthly_budget = st.text_input("Monthly Operating Budget", placeholder="e.g. Rs. 3 lakh")
        main_issue = st.selectbox(
            "Main Business Challenge",
            [
                "How to grow the company",
                "Corporate financial problems",
                "How to save the company from crisis",
                "How to run with a low budget",
                "Need an overall company analysis"
            ]
        )
        target = st.text_input("Main Goal for the Next 6-12 Months", placeholder="e.g. reach break-even or increase sales")
        constraints = st.text_area("Known Problems or Constraints", height=100, placeholder="Debt, falling sales, high costs, cash-flow gap, competition...")

    if st.button("📊 Analyze Company & Create Action Plan", type="primary"):
        if not company_type.strip() or not target.strip():
            st.warning("Please enter the company/industry and your main goal.")
        else:
            query = f"""
Company strategy and financial health analysis for {company_type}.
Stage: {company_stage}. Team size: {team_size}. Monthly revenue: {monthly_revenue}.
Monthly operating budget: {monthly_budget}. Main challenge: {main_issue}.
Six to twelve month goal: {target}. Constraints: {constraints}.
"""
            with st.spinner("Analyzing company information with RAG and Ollama..."):
                rag_context, sources = rag_pipeline.retrieve_context(
                    query,
                    limit=5,
                    category_filter="All",
                    tenant_id_filter=tenant_id
                )
                knowledge = f"Retrieved company knowledge:\n{rag_context}" if rag_context else "No company-specific documents were retrieved."
                prompt = f"""
Analyze this company and create a practical management plan.

{query}
{knowledge}

Cover:
1. Company diagnosis: strengths, risks, and the first metrics to measure.
2. Growth strategy: customers, sales channels, pricing, product, and partnerships.
3. Corporate financial issues: cash flow, runway, receivables, payables, costs, debt, and break-even.
4. Crisis survival plan: actions for the next 7, 30, and 90 days.
5. Low-budget operating plan: essential costs, cuts to avoid, automation, and priorities.
6. A ranked action table with action, owner, timeframe, estimated cost impact, and success metric.

Use retrieved documents when available. Do not invent financial figures, legal/tax advice, market statistics, or guaranteed growth. Clearly mark assumptions and recommend a qualified accountant or legal adviser for regulated decisions.
"""
                response = llm_client.generate(
                    prompt,
                    system_prompt=(
                        "You are a cautious corporate strategy and financial planning adviser. "
                        "Give practical, evidence-based recommendations and state assumptions clearly."
                    )
                )

            st.markdown("### 🧭 Company Analysis & Action Plan")
            st.markdown(response)
            if sources:
                st.markdown("---")
                st.markdown("#### 📚 Retrieved Business Sources")
                for source in sources:
                    st.caption(
                        f"- 📄 {source['document_name']} ({source['category']}) - "
                        f"Match: {source['relevance_score']}%"
                    )
