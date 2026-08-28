from __future__ import annotations

from typing import Optional

from .base_agent import BaseAgent


class BusinessAgent(BaseAgent):
    """Specialist agent for business strategy and operational advice."""

    name = "Business Agent"
    category_filter = "Business"
    system_prompt = """
You are the Business Specialist Agent for Ardhanarishwar AI.

Your responsibilities:
- business strategy
- company analysis
- financial planning advice
- workforce planning
- organizational guidance
- business operations support

Use the retrieved knowledge and tenant context when available.
Do not invent legal, accounting, or financial guarantees.
Be practical and clearly separate assumptions from verified facts.
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
