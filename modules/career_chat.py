from typing import Dict, Any

import streamlit as st

from core.router import ai_orchestrator
from database.models import (
    create_conversation,
    get_conversation_messages,
    get_user_conversations,
    record_feedback,
)


def render_career_chat(current_user: Dict[str, Any]):
    """Render the retained LangGraph-powered candidate career assistant."""
    if current_user.get("role") != "Candidate":
        st.error("The career assistant is available to candidates only.")
        return

    conversations = get_user_conversations(current_user["id"])
    if not conversations:
        conversation_id = create_conversation(
            current_user["id"], current_user["tenant_id"], "Candidate", "Career Assistant"
        )
        conversations = get_user_conversations(current_user["id"])
        st.session_state["career_chat_id"] = conversation_id
    elif st.session_state.get("career_chat_id") not in {item["id"] for item in conversations}:
        st.session_state["career_chat_id"] = conversations[0]["id"]

    left, right = st.columns([1, 3])
    with left:
        if st.button("New chat", key="career_chat_new"):
            st.session_state["career_chat_id"] = create_conversation(
                current_user["id"], current_user["tenant_id"], "Candidate", "Career Assistant"
            )
            st.rerun()
        for conversation in conversations:
            if st.button(
                conversation["title"][:24],
                key=f"career_chat_{conversation['id']}",
                use_container_width=True,
            ):
                st.session_state["career_chat_id"] = conversation["id"]
                st.rerun()

    conversation_id = st.session_state["career_chat_id"]
    with right:
        messages = get_conversation_messages(conversation_id)
        for message in messages:
            with st.chat_message(message["sender"]):
                st.markdown(message["content"])

        if len(messages) >= 2 and messages[-2]["sender"] == "user" and messages[-1]["sender"] == "assistant":
            feedback_col1, feedback_col2, _ = st.columns([1, 1, 6])
            if feedback_col1.button("Helpful", key=f"career_feedback_up_{messages[-1]['id']}"):
                if record_feedback(current_user, messages[-2]["content"], messages[-1]["content"], 1):
                    st.toast("Thanks for your feedback.")
            if feedback_col2.button("Not helpful", key=f"career_feedback_down_{messages[-1]['id']}"):
                if record_feedback(current_user, messages[-2]["content"], messages[-1]["content"], -1):
                    st.toast("Thanks for your feedback.")

        prompt = st.chat_input("Ask about your career, resume, skills, or interviews")
        if prompt:
            response = ai_orchestrator.process_request(
                query=prompt,
                user_id=current_user["id"],
                conversation_id=conversation_id,
                tenant_id=current_user["tenant_id"],
                user_role=current_user["role"],
            )
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                st.markdown(response)
