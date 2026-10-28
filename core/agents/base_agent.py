from __future__ import annotations

from typing import Optional

from core.llm import llm_client


class BaseAgent:
    """Common interface for all specialist agents."""

    name = "Base Agent"
    system_prompt = "You are a helpful AI assistant."
    def __init__(self):
        self.name = self.name

    def build_prompt(
        self,
        query: str,
        profile_context: Optional[str] = None,
    ) -> str:
        profile_block = (
            f"User profile context:\n{profile_context}\n\n"
            if profile_context
            else ""
        )
        return (
            f"{profile_block}"
            f"User question: {query}\n\n"
            "Answer clearly, and distinguish general guidance from facts that need verification."
        )

    def run(self, query: str, profile_context: Optional[str] = None) -> str:
        response = llm_client.generate(
            self.build_prompt(query=query, profile_context=profile_context),
            system_prompt=self.system_prompt,
            temperature=0.4,
        )
        return response


__all__ = ["BaseAgent"]
