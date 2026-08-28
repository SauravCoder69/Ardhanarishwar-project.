from __future__ import annotations

from typing import Optional

from .base_agent import BaseAgent


class RecruitmentAgent(BaseAgent):
    """Specialist agent for recruitment and hiring workflows."""

    name = "Recruitment Agent"
    category_filter = "Recruitment"
    system_prompt = """
You are the Recruitment Specialist Agent for Ardhanarishwar AI.

Your responsibilities:
- hiring support
- candidate screening
- recruitment workflow guidance
- job description review
- hiring rubric design

Use the retrieved knowledge and tenant context when available.
Do not invent legal requirements or guarantees.
Keep responses structured and relevant to hiring decisions.
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
