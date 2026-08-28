from typing import Any, Dict, List, Optional, Tuple

from core.graph import run_agent_graph


class SupervisorAgent:
    """Thin supervisor boundary between the router and LangGraph."""

    def run(
        self,
        query: str,
        profile_context: str,
        tenant_id: Optional[str],
        agent_name: Optional[str] = None,
        category_filter: Optional[str] = None,
        user_role: Optional[str] = None,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Execute the specialist agent via the LangGraph-backed routing flow."""
        response_text, sources, actual_name = run_agent_graph(
            query=query,
            profile_context=profile_context,
            tenant_id=tenant_id,
            agent_name=agent_name or "General Assistant",
            category_filter=category_filter,
            user_role=user_role,
        )
        return response_text, sources


supervisor_agent = SupervisorAgent()
