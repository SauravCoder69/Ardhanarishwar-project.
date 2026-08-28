from __future__ import annotations

from typing import Optional

from .base_agent import BaseAgent


class InterviewAgent(BaseAgent):
    """Specialist agent for interviews and mock interview preparation."""

    name = "Interview Agent"
    category_filter = "Interviews"
    system_prompt = """
You are the Interview Specialist Agent for Ardhanarishwar AI.

Your responsibilities:
- interview preparation
- technical interview coaching
- behavioral interview help
- mock interview guidance
- answer framing and feedback

Use the retrieved knowledge and user profile when available.
Do not invent company-specific facts or guaranteed outcomes.
Keep responses structured and practical.
""".strip()

    def run(
        self,
        query: str,
        user_id: Optional[int] = None,
        tenant_id: Optional[str] = None,
        user_role: Optional[str] = None,
        category_filter: Optional[str] = None,
        profile_context: Optional[str] = None,
        conversation_context: Optional[str] = None,
    ):
        return super().run(
            query=query,
            user_id=user_id,
            tenant_id=tenant_id,
            user_role=user_role,
            category_filter=category_filter,
            profile_context=profile_context,
            conversation_context=conversation_context,
        )
