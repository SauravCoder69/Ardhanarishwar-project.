from __future__ import annotations

from typing import Optional

from .base_agent import BaseAgent


class GeneralAssistantAgent(BaseAgent):
    """General-purpose assistant for non-specialized queries."""

    name = "General Assistant"
    category_filter = None
    system_prompt = """
You are the General Assistant for Ardhanarishwar AI.

Respond to general questions clearly and helpfully.
Use retrieved context when available, but avoid overcomplicating general replies.
If the request fits a specialist domain, suggest the relevant specialist agent.
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
