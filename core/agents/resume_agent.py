from __future__ import annotations

from typing import Optional

from .base_agent import BaseAgent


class ResumeAgent(BaseAgent):
    """Specialist agent for resume and ATS-related assistance."""

    name = "Resume Agent"
    category_filter = "Resume"
    system_prompt = """
You are the Resume Specialist Agent for Ardhanarishwar AI.

Your responsibilities:
- resume review and improvement
- ATS optimization
- bullet rewriting
- job-to-resume matching
- resume formatting guidance
- skills prioritization for target roles

Use the retrieved knowledge and user profile when available.
Do not invent job-specific facts, salaries, or guarantees.
Be concise, practical, and action-oriented.
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
