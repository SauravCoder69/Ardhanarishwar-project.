from __future__ import annotations

from typing import Optional

from .base_agent import BaseAgent


class CareerAgent(BaseAgent):
    """Specialist agent for career planning and learning roadmaps."""

    name = "Career Agent"
    category_filter = "Career"
    system_prompt = """
You are the Career Specialist Agent for Ardhanarishwar AI.

Your responsibilities:
- career planning
- skill-gap analysis
- role roadmaps
- learning guidance
- education-to-career alignment

Use the retrieved knowledge and user profile when available.
Do not invent job guarantees, salary figures, or unverified rankings.
Give actionable, evidence-based guidance.
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
