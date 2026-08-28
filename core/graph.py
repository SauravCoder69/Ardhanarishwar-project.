from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict

try:
    from langgraph.graph import END, START, StateGraph

    LANGGRAPH_AVAILABLE = True
except Exception:
    LANGGRAPH_AVAILABLE = False
    END = START = None
    StateGraph = None

from core.agents.registry import get_agent


AGENT_ROLE_ACCESS = {
    "Resume Agent": {"Candidate", "Admin"},
    "Interview Agent": {"Candidate", "Admin"},
    "Career Agent": {"Candidate", "Admin"},
    "Recruitment Agent": {"Business", "Admin"},
    "Business Agent": {"Business", "Admin"},
    "General Assistant": {"Candidate", "Business", "Admin"},
}


def _authorization_error(agent_name: str, user_role: Optional[str]) -> Optional[str]:
    allowed_roles = AGENT_ROLE_ACCESS.get(agent_name)
    if not user_role:
        return "A user role is required to use this specialist agent."
    if not allowed_roles or user_role not in allowed_roles:
        return "You are not authorized to use this specialist agent."
    return None


class AgentGraphState(TypedDict):
    query: str
    profile_context: str
    tenant_id: Optional[str]
    user_role: Optional[str]
    category_filter: Optional[str]
    agent_name: str
    response: str
    sources: List[Dict[str, Any]]
    agent_label: str


def _specialist_node(state: Dict[str, Any]) -> Dict[str, Any]:
    agent_name = state.get("agent_name") or "General Assistant"
    user_role = state.get("user_role")
    authorization_error = _authorization_error(agent_name, user_role)
    if authorization_error:
        return {
            "response": authorization_error,
            "sources": [],
            "agent_label": "Authorization Guard",
        }

    agent = get_agent(agent_name)
    response_text, sources, actual_name = agent.run(
        query=state["query"],
        tenant_id=state.get("tenant_id"),
        user_role=user_role,
        category_filter=state.get("category_filter"),
        profile_context=state.get("profile_context"),
    )
    return {
        "response": response_text,
        "sources": sources,
        "agent_label": actual_name,
    }


def run_agent_graph(
    query: str,
    profile_context: str,
    tenant_id: Optional[str],
    agent_name: str,
    category_filter: Optional[str] = None,
    user_role: Optional[str] = None,
) -> tuple[str, List[Dict[str, Any]], str]:
    if not tenant_id:
        return "A tenant is required to retrieve knowledge safely.", [], "Tenant Guard"

    authorization_error = _authorization_error(agent_name, user_role)
    if authorization_error:
        return authorization_error, [], "Authorization Guard"

    if not LANGGRAPH_AVAILABLE or StateGraph is None:
        agent = get_agent(agent_name)
        response_text, sources, actual_name = agent.run(
            query=query,
            tenant_id=tenant_id,
            user_role=user_role,
            category_filter=category_filter,
            profile_context=profile_context,
        )
        return response_text, sources, actual_name

    try:
        graph = StateGraph(AgentGraphState)
        graph.add_node("specialist", _specialist_node)
        graph.add_edge(START, "specialist")
        graph.add_edge("specialist", END)

        app = graph.compile()
        result = app.invoke(
            {
                "query": query,
                "profile_context": profile_context or "",
                "tenant_id": tenant_id,
                "user_role": user_role,
                "category_filter": category_filter,
                "agent_name": agent_name,
            }
        )
        return result.get("response", ""), result.get("sources", []), result.get("agent_label", agent_name)
    except (TypeError, ValueError, RuntimeError) as exc:
        return (
            f"LangGraph execution failed: {exc}",
            [],
            "Graph Error",
        )


__all__ = ["run_agent_graph", "LANGGRAPH_AVAILABLE"]