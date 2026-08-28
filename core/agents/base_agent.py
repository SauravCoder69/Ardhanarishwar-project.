from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from core.llm import llm_client
from core.rag import rag_pipeline


class BaseAgent:
    """Common interface for all specialist agents."""

    name = "Base Agent"
    system_prompt = "You are a helpful AI assistant."
    category_filter: Optional[str] = None
    default_limit = 3

    def __init__(self):
        self.name = self.name

    def retrieve_context(
        self,
        query: str,
        tenant_id: Optional[str] = None,
        category_filter: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        effective_limit = limit or self.default_limit
        effective_filter = category_filter or self.category_filter

        if effective_filter and effective_filter != "All":
            return rag_pipeline.retrieve_context(
                query,
                limit=effective_limit,
                category_filter=effective_filter,
                tenant_id_filter=tenant_id,
            )

        return rag_pipeline.retrieve_context(
            query,
            limit=effective_limit,
            tenant_id_filter=tenant_id,
        )

    def build_prompt(
        self,
        query: str,
        profile_context: Optional[str] = None,
        retrieved_context: str = "",
    ) -> str:
        context_block = (
            "Retrieved knowledge from approved tenant documents:\n"
            f"{retrieved_context}\n\n"
            if retrieved_context
            else ""
        )
        profile_block = (
            f"User profile context:\n{profile_context}\n\n"
            if profile_context
            else ""
        )
        return (
            f"{profile_block}"
            f"{context_block}"
            f"User question: {query}\n\n"
            "Answer clearly and use the retrieved context when relevant."
        )

    def run(
        self,
        query: str,
        user_id: Optional[int] = None,
        tenant_id: Optional[str] = None,
        user_role: Optional[str] = None,
        category_filter: Optional[str] = None,
        profile_context: Optional[str] = None,
        conversation_context: Optional[str] = None,
    ) -> Tuple[str, List[Dict[str, Any]], str]:
        retrieved_context, sources = self.retrieve_context(
            query,
            tenant_id=tenant_id,
            category_filter=category_filter,
        )

        prompt = self.build_prompt(
            query=query,
            profile_context=profile_context,
            retrieved_context=retrieved_context,
        )

        response = llm_client.generate(
            prompt,
            system_prompt=self.system_prompt,
            temperature=0.4,
        )
        return response, sources, self.name


__all__ = ["BaseAgent"]
