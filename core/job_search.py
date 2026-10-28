import json
import re
from typing import Any, Dict

from core.llm import llm_client

JOB_TYPES = {"Full-time", "Part-time", "Contract", "Internship", "Temporary", "Remote"}
FILTER_KEYS = {"role", "location", "skills", "experience", "job_type"}


def validate_job_filters(value: Any) -> Dict[str, Any]:
    """Validate and normalize the filter object returned by the copilot."""
    if not isinstance(value, dict) or set(value) - FILTER_KEYS:
        raise ValueError("The copilot returned invalid search filters.")

    filters: Dict[str, Any] = {
        "role": "",
        "location": "",
        "skills": [],
        "experience": "",
        "job_type": "",
    }
    for key in ("role", "location", "experience"):
        field = value.get(key, "")
        if not isinstance(field, str) or len(field) > 120:
            raise ValueError(f"The {key} search filter must be a short text value.")
        filters[key] = field.strip()

    skills = value.get("skills", [])
    if not isinstance(skills, list) or len(skills) > 12 or any(
        not isinstance(skill, str) or not skill.strip() or len(skill) > 60
        for skill in skills
    ):
        raise ValueError("Skills must be a list of up to 12 short text values.")
    filters["skills"] = [skill.strip() for skill in skills]

    job_type = value.get("job_type", "")
    if not isinstance(job_type, str):
        raise ValueError("The job type filter must be text.")
    if job_type and job_type not in JOB_TYPES:
        raise ValueError("The copilot selected an unsupported job type.")
    filters["job_type"] = job_type
    return filters


def parse_job_search_query(query: str) -> Dict[str, Any]:
    """Translate natural language into a constrained, validated job filter object."""
    if not query.strip():
        raise ValueError("Enter a job-search request first.")
    if len(query) > 1000:
        raise ValueError("Keep the job-search request under 1,000 characters.")
    response = llm_client.generate(
        query,
        system_prompt=(
            "Convert the candidate's job search request into one JSON object with exactly "
            "these optional fields: role (string), location (string), skills (array of strings), "
            "experience (string), job_type (string). Use job_type only as one of "
            "Full-time, Part-time, Contract, Internship, Temporary, Remote. "
            "Do not add explanations or other fields. Use empty strings and an empty array "
            "for filters not specified. Never infer protected personal attributes."
        ),
        temperature=0,
    )
    match = re.search(r"\{.*\}", response, re.DOTALL)
    if not match:
        raise ValueError("The AI copilot did not return valid JSON filters. Please try again.")
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise ValueError("The AI copilot returned malformed filters. Please try again.") from exc
    return validate_job_filters(parsed)
