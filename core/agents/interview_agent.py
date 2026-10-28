from __future__ import annotations

from typing import Optional

from .base_agent import BaseAgent


class InterviewAgent(BaseAgent):
    """Specialist agent for interviews and mock interview preparation."""

    name = "Interview Agent"
    system_prompt = """
You are the Interview Specialist Agent for Ardhanarishwar AI.

Your responsibilities:
- interview preparation
- technical interview coaching
- behavioral interview help
- mock interview guidance
- answer framing and feedback

Use the user profile when available.
Do not invent company-specific facts or guaranteed outcomes.
Keep responses structured and practical.
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
