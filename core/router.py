from core.llm import llm_client
from core.memory import memory_manager
from core.agentic import supervisor_agent
from config import ROLE_CANDIDATE, ROLE_ADMIN
from database.models import user_matches_tenant
from typing import Optional


class AIOrchestrator:

    def detect_intent(self, query: str) -> str:

        system_prompt = """
You are the Intent Classification Engine for an AI Career Assistant.

Understand the complete meaning and context of the user's query and
classify its PRIMARY intent into exactly ONE available agent.

AVAILABLE AGENTS:

1. Resume Agent
- Resume or CV creation, review, rewriting, or improvement
- ATS optimization
- Resume bullet points
- Resume formatting
- Resume-job description matching

2. Interview Agent
- Interview preparation
- Mock interviews
- Technical interview preparation
- Coding interview preparation
- Behavioral interview preparation
- Interview-specific questions and strategies

3. Career Agent
- Career planning and career advice
- Learning roadmaps
- Skill development and skill-gap analysis
- Education and professional growth
- Programming and software development
- Python, Java, C++, JavaScript, TypeScript, SQL
- AI, Machine Learning, Deep Learning, Data Science
- Cloud, Databases, Git, APIs
- Frontend, Backend, Web Development

4. General Assistant
- Casual conversation
- Requests outside the candidate career domain

CLASSIFICATION RULES:

- Understand the complete query instead of matching individual words.
- Do not use keyword matching as the primary classification method.
- Identify what the user is actually trying to accomplish.
- Select exactly ONE agent.
- If multiple domains are mentioned, select the agent responsible
  for the user's PRIMARY goal.
- Resume-related actions belong to Resume Agent.
- Interview-specific preparation belongs to Interview Agent.
- Programming and technology questions belong to Career Agent unless
  they are specifically related to interview preparation.
- Casual or unrelated questions belong to General Assistant.
- If the intent is unclear, select General Assistant.
- Never invent a new agent.

Return ONLY one of these exact values:

Resume Agent
Interview Agent
Career Agent
General Assistant
"""

        raw_classification = llm_client.generate(
            query,
            system_prompt=system_prompt,
            temperature=0,
            timeout=15
        ).strip()

        valid_agents = {
            "Resume Agent",
            "Interview Agent",
            "Career Agent",
            "General Assistant"
        }

        # Clean raw output from LLM (strip quotes, markdown tags, punctuation)
        cleaned = raw_classification.replace("*", "").replace("`", "").replace('"', '').replace("'", "").strip()
        cleaned = cleaned.rstrip(".").rstrip(":").strip()
        if len(cleaned) > 3 and cleaned[:2].isdigit() and cleaned[2] == ".":
            cleaned = cleaned[3:].strip()

        # Check exact match (case-insensitive)
        for agent in valid_agents:
            if cleaned.lower() == agent.lower():
                return agent

        # Check substring match
        for agent in valid_agents:
            if agent.lower() in cleaned.lower():
                return agent

        # Heuristic rule-based fallback if LLM classification fails or returns fallback
        q_lower = query.lower()
        if any(k in q_lower for k in ["interview", "mock", "behavioral", "technical interview", "coding interview"]):
            return "Interview Agent"
        if any(k in q_lower for k in ["resume", "resumes", "cv", "ats", "bullet point", "portfolio"]):
            return "Resume Agent"
        if any(k in q_lower for k in ["career", "roadmap", "learning", "skill", "skills", "job", "java", "python", "coding", "software engineer", "developer", "learn", "growth", "education"]):
            return "Career Agent"

        return "General Assistant"

    def process_request(
        self,
        query: str,
        user_id: int,
        conversation_id: Optional[int] = None,
        tenant_id: Optional[str] = None,
        user_role: Optional[str] = None
    ) -> str:
        if not tenant_id:
            return "A tenant is required to process this request safely."
        if user_role not in (ROLE_CANDIDATE, ROLE_ADMIN) or not user_matches_tenant(
            user_id, tenant_id, user_role
        ):
            return "The authenticated account does not match the requested tenant."

        agent_name = self.detect_intent(query)

        if user_role == ROLE_CANDIDATE and agent_name == "General Assistant":
            return (
                "I can only help with career-related questions, such as resumes, "
                "skills, learning paths, interviews, and job searches."
            )

        profile_context = memory_manager.get_user_profile_context(user_id)

        response_text = supervisor_agent.run(
            query=query,
            profile_context=profile_context,
            agent_name=agent_name,
            user_role=user_role,
        )

        if conversation_id:
            memory_manager.save_chat_turn(
                conversation_id,
                query,
                response_text
            )

        return response_text


ai_orchestrator = AIOrchestrator()
