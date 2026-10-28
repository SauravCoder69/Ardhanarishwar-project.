from __future__ import annotations

from typing import Any, Dict, Optional, TypedDict

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
    "General Assistant": {"Candidate", "Admin"},
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
    user_role: Optional[str]
    agent_name: str
    response: str


def _specialist_node(state: Dict[str, Any]) -> Dict[str, Any]:
    agent_name = state.get("agent_name") or "General Assistant"
    user_role = state.get("user_role")
    authorization_error = _authorization_error(agent_name, user_role)
    if authorization_error:
        return {"response": authorization_error}

    agent = get_agent(agent_name)
    response_text = agent.run(
        query=state["query"],
        profile_context=state.get("profile_context"),
    )
    return {"response": response_text}


def run_agent_graph(
    query: str,
    profile_context: str,
    agent_name: str,
    user_role: Optional[str] = None,
) -> str:
    authorization_error = _authorization_error(agent_name, user_role)
    if authorization_error:
        return authorization_error

    if not LANGGRAPH_AVAILABLE or StateGraph is None:
        agent = get_agent(agent_name)
        return agent.run(
            query=query,
            profile_context=profile_context,
        )

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
                "user_role": user_role,
                "agent_name": agent_name,
            }
        )
        return result.get("response", "")
    except (TypeError, ValueError, RuntimeError) as exc:
        return f"LangGraph execution failed: {exc}"


__all__ = ["run_agent_graph", "LANGGRAPH_AVAILABLE"]