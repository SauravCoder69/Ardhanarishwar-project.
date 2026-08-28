from __future__ import annotations

from typing import Dict, Type

from .business_agent import BusinessAgent
from .career_agent import CareerAgent
from .general_assistant_agent import GeneralAssistantAgent
from .interview_agent import InterviewAgent
from .recruitment_agent import RecruitmentAgent
from .resume_agent import ResumeAgent


AGENT_REGISTRY: Dict[str, Type] = {
    "resume": ResumeAgent,
    "interview": InterviewAgent,
    "career": CareerAgent,
    "recruitment": RecruitmentAgent,
    "business": BusinessAgent,
    "general": GeneralAssistantAgent,
}


def get_agent(agent_name: str):
    key = (agent_name or "").strip().lower().replace(" ", "_")
    if key in AGENT_REGISTRY:
        return AGENT_REGISTRY[key]()

    if agent_name and agent_name.lower() == "resume agent":
        return ResumeAgent()
    if agent_name and agent_name.lower() == "interview agent":
        return InterviewAgent()
    if agent_name and agent_name.lower() == "career agent":
        return CareerAgent()
    if agent_name and agent_name.lower() == "recruitment agent":
        return RecruitmentAgent()
    if agent_name and agent_name.lower() == "business agent":
        return BusinessAgent()
    if agent_name and agent_name.lower() == "general assistant":
        return GeneralAssistantAgent()

    return GeneralAssistantAgent()


__all__ = ["AGENT_REGISTRY", "get_agent"]
