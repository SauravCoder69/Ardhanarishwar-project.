# ⚡ Ardhanarishwar AI

> **Enterprise Multi-Agent Platform for Candidate Career Growth & HR Recruitment**

🌐 **Live Deployment**: [https://ardhanarishwar.streamlit.app/](https://ardhanarishwar.streamlit.app/)

---

## 🤖 Specialist AI Agent Architecture

Ardhanarishwar uses a **LangGraph-powered Multi-Agent Router** that classifies intent and delegates requests to 5 specialized AI agents:

| Agent Name | Core Responsibility & Function |
|---|---|
| 🎤 **Interview Agent** | Technical & behavioral mock interviews, 3D answer evaluation (Accuracy, Relevance, Communication). |
| 📝 **Resume Agent** | ATS compatibility scoring (0–100%), skill extraction, and CV-to-Job Description matching. |
| 🎓 **Career Agent** | Competency gap analysis, personalized 30-day skill roadmaps, and career counselling. |
| 💼 **Recruitment Agent** | AI JD requirement extraction, batch candidate resume ranking, and interview screening questions. |
| 🏢 **Business Agent** | Executive business strategy, 13-week cash flow forecasting, and operational planning. |
| 🤖 **General Assistant** | Casual career conversation and general domain assistance. |

---

## 🌟 Key Platform Capabilities

### 🎓 Candidate Ecosystem
- **ATS Resume Analyzer**: Instant ATS compatibility score (0-100%) and skill-gap recommendations.
- **Interactive Mock Interviews**: AI interview practice with real-time scoring out of 100.
- **Job Portal & Live HR Status**: Apply for jobs and track shortlisting status (`Shortlisted`, `Interview Scheduled`).

### 💼 Business & HR Ecosystem
- **JD Requirement Extractor**: Automatically extract required skills, experience, and responsibilities from JDs.
- **Batch Candidate Leaderboard**: Rank multiple candidate resumes against job descriptions (`Strong Fit ≥80%`, `Moderate Fit`, `Weak Fit`).
- **HR Candidate Shortlisting**: Shortlist top candidates with real-time notification alerts sent to candidate dashboards.

### ⚡ Admin Command Center
- **Enterprise RAG Knowledge Base**: Upload domain PDFs/DOCX files into **Qdrant Vector DB** for role-aware retrieval.
- **Unanswered Queries Review**: Track and resolve candidate questions missing from the knowledge base.
- **Platform Analytics**: Monitor active users, conversation history, and positive vs. negative feedback (👍/👎).

---

## 🛠️ Technology Stack

- **UI & Frontend**: Streamlit
- **Agent Orchestration**: LangGraph `StateGraph` & AI Router
- **Vector Search (RAG)**: Qdrant Vector DB + `all-MiniLM-L6-v2` Embeddings
- **LLM Engine**: Local Ollama Inference (`llama3.2`) + Heuristic Fallback Engine
- **Database**: SQLite (Multi-tenant schema with SHA-256 Auth)

---

## 🔑 Demo Credentials

- 🎓 **Candidate**: `candidate` / `cand123`
- 💼 **Business**: `business` / `biz123`
- ⚡ **Admin**: `admin` / `admin123`

---

## 🚀 Quick Start (Local Setup)

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```
