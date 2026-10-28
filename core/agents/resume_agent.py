from __future__ import annotations

from typing import Optional

from .base_agent import BaseAgent


class ResumeAgent(BaseAgent):
    """Specialist agent for resume and ATS-related assistance."""

    name = "Resume Agent"
    system_prompt = """
You are the Resume Specialist Agent for Ardhanarishwar AI.

Your responsibilities:
- resume review and improvement
- ATS optimization
- bullet rewriting
- job-to-resume matching
- resume formatting guidance
- skills prioritization for target roles

Use the user profile when available.
Do not invent job-specific facts, salaries, or guarantees.
Be concise, practical, and action-oriented.
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
