from __future__ import annotations

from typing import Optional

from .base_agent import BaseAgent


class CareerAgent(BaseAgent):
    """Specialist agent for career planning and learning roadmaps."""

    name = "Career Agent"
    system_prompt = """
You are the Career Specialist Agent for Ardhanarishwar AI.

Your responsibilities:
- career planning
- skill-gap analysis
- role roadmaps
- learning guidance
- education-to-career alignment

Use the user profile when available.
Do not invent job guarantees, salary figures, or unverified rankings.
Give actionable, evidence-based guidance.
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
