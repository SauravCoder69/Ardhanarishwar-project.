from core.llm import llm_client
from core.rag import rag_pipeline
from core.memory import memory_manager
from typing import Dict, Any, Tuple, List, Optional

class AIOrchestrator:
    """
    AI Router & Orchestrator that detects user intent, injects profile memory,
    performs RAG knowledge retrieval, and invokes the appropriate domain agent.
    """

    def detect_intent(self, query: str) -> str:
        """Classify user query into domain intents."""
        q = query.lower()
        if any(w in q for w in ["resume", "cv", "ats", "bullet point", "job description match"]):
            return "Resume Agent"
        elif any(w in q for w in ["interview", "mock", "technical question", "coding question", "behavioral"]):
            return "Interview Agent"
        elif any(w in q for w in ["career", "roadmap", "learn", "skill gap", "technology stack", "path"]):
            return "Career Agent"
        elif any(w in q for w in ["recruitment", "hiring", "candidate screening", "job description create", "hr"]):
            return "Recruitment Agent"
        elif any(w in q for w in ["business", "workforce", "process", "company", "budget"]):
            return "Business Agent"
        else:
            return "General Assistant"

    def process_request(
        self,
        query: str,
        user_id: int,
        conversation_id: Optional[int] = None,
        category_filter: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> Tuple[str, List[Dict[str, Any]], str]:
        """
        Main execution flow:
        1. Detect intent agent
        2. Fetch user profile memory
        3. Retrieve relevant knowledge from Qdrant via RAG with tenant data isolation
        4. Construct domain prompt
        5. Invoke local Ollama LLM
        6. Persist message turn in DB memory
        """
        agent_name = self.detect_intent(query)
        profile_context = memory_manager.get_user_profile_context(user_id)
        
        # RAG Knowledge Retrieval with tenant isolation
        rag_context, sources = rag_pipeline.retrieve_context(
            query,
            limit=3,
            category_filter=category_filter,
            tenant_id_filter=tenant_id
        )

        # Build Domain System Prompt
        system_prompt = f"""
You are Ardhanarishwar AI, an expert SaaS Assistant specializing in Careers, Education, Recruitment, and Business Intelligence.
Current Active Agent: {agent_name}

{profile_context}

Guidance:
- Give professional, direct, structured, actionable answers with clear headings and bullet points.
- If relevant retrieved knowledge context is provided below, incorporate it explicitly.
- Never make up fake stats or lie.
"""

        full_prompt = f"User Question: {query}\n"
        if rag_context:
            full_prompt = f"Retrieved Knowledge Context (from Qdrant Vector Store):\n{rag_context}\n\n" + full_prompt

        # Generate LLM response
        response_text = llm_client.generate(full_prompt, system_prompt=system_prompt)

        # Save turn to conversation memory if conversation_id provided
        if conversation_id:
            memory_manager.save_chat_turn(conversation_id, query, response_text, sources)

        return response_text, sources, agent_name

# Global Orchestrator Instance
ai_orchestrator = AIOrchestrator()
