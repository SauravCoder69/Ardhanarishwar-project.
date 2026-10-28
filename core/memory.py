from database.models import get_candidate_profile, save_message
from typing import Dict, Any

class MemoryManager:
    """Manages Short-Term Conversation History and Long-Term Candidate Profile Memory."""

    def get_user_profile_context(self, user_id: int) -> str:
        """Format candidate profile facts into a system context snippet for personalisation."""
        profile = get_candidate_profile(user_id)
        if not profile or not profile.get('career_goal'):
            return "User Profile: General Candidate."

        return (
            f"User Profile Memory:\n"
            f"- Name/Role Goal: {profile.get('career_goal', 'Not specified')} (Target Role: {profile.get('preferred_role', 'N/A')})\n"
            f"- Current Skills: {profile.get('current_skills', 'N/A')}\n"
            f"- Education: {profile.get('education', 'N/A')}\n"
            f"- Experience Level: {profile.get('experience', 'N/A')}\n"
            f"- Learning Interests: {profile.get('learning_interests', 'N/A')}\n"
        )

    def save_chat_turn(self, conversation_id: int, user_query: str, assistant_response: str):
        """Persist user query and assistant answer into database."""
        save_message(conversation_id, "user", user_query)
        save_message(conversation_id, "assistant", assistant_response)


memory_manager = MemoryManager()
