from __future__ import annotations

from typing import Optional

from .base_agent import BaseAgent


class GeneralAssistantAgent(BaseAgent):
    """General-purpose assistant for non-specialized queries."""

    name = "General Assistant"
    system_prompt = """
You are the General Assistant for Ardhanarishwar AI.

Respond to general questions clearly and helpfully.
Avoid overcomplicating general replies.
If the request fits a specialist domain, suggest the relevant specialist agent.
""".strip()

    def run(
        self,
        query: str,
        profile_context: Optional[str] = None,
    ) -> str:
        return super().run(
            query=query,
            profile_context=profile_context,
        )
