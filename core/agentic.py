from typing import Optional

from core.graph import run_agent_graph


class SupervisorAgent:
    """Thin supervisor boundary between the router and LangGraph."""

    def run(
        self,
        query: str,
        profile_context: str,
        agent_name: Optional[str] = None,
        user_role: Optional[str] = None,
    ) -> str:
        """Execute the specialist agent via the LangGraph-backed routing flow."""
        return run_agent_graph(
            query=query,
            profile_context=profile_context,
            agent_name=agent_name or "General Assistant",
            user_role=user_role,
        )


supervisor_agent = SupervisorAgent()
