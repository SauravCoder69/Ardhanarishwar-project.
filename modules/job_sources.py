import html
import re
from typing import Any, Dict, List

import requests


class ArbeitnowSource:
    """Fetch normalized job listings from Arbeitnow's public job-board API."""

    name = "arbeitnow"
    endpoint = "https://www.arbeitnow.com/api/job-board-api"

    def fetch(self, page: int = 1) -> List[Dict[str, Any]]:
        response = requests.get(self.endpoint, params={"page": page}, timeout=15)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
            raise ValueError("Arbeitnow returned an unexpected response format.")

        normalized = []
        for item in payload["data"]:
            if not isinstance(item, dict):
                continue
            job_url = item.get("url")
            source_id = item.get("slug") or job_url
            title = item.get("title")
            company_name = item.get("company_name")
            if not all(isinstance(value, str) and value.strip() for value in (job_url, source_id, title, company_name)):
                continue
            if not job_url.startswith("https://"):
                continue

            tags = item.get("tags") or []
            job_types = item.get("job_types") or []
            if not isinstance(tags, list):
                tags = []
            if not isinstance(job_types, list):
                job_types = []
            description = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", str(item.get("description", ""))))).strip()
            remote = bool(item.get("remote"))
            experience = _infer_experience(title, description)
            normalized_types = _normalize_job_types(job_types, remote)
            normalized.append({
                "source": self.name,
                "source_id": source_id.strip(),
                "company_name": company_name.strip(),
                "title": title.strip(),
                "description": description,
                "required_skills": ", ".join(str(tag).strip() for tag in tags if str(tag).strip()),
                "experience": experience,
                "salary": "",
                "location": str(item.get("location") or "").strip(),
                "job_type": normalized_types,
                "job_url": job_url.strip(),
                "remote": remote,
                "posted_at": str(item.get("created_at") or ""),
            })
        return normalized


def _infer_experience(title: str, description: str) -> str:
    text = f"{title} {description}".lower()
    if re.search(r"\b(intern|graduate|junior|entry[- ]level|0\s*[-–]\s*2 years?)\b", text):
        return "Entry-level"
    if re.search(r"\b(senior|lead|principal|staff|5\+ years?|6\+ years?)\b", text):
        return "Senior"
    if re.search(r"\b(mid[- ]level|3\s*[-–]\s*5 years?|2\s*[-–]\s*5 years?)\b", text):
        return "Mid-level"
    return ""

def _normalize_job_types(job_types: List[Any], remote: bool) -> str:
    type_aliases = {
        "full time": "Full-time",
        "full-time": "Full-time",
        "part time": "Part-time",
        "part-time": "Part-time",
        "contract": "Contract",
        "internship": "Internship",
        "temporary": "Temporary",
        "remote": "Remote",
    }
    normalized = []
    for kind in job_types:
        value = str(kind).strip()
        canonical = type_aliases.get(value.lower().replace("_", " "), value)
        if canonical and canonical not in normalized:
            normalized.append(canonical)
    if remote and "Remote" not in normalized:
        normalized.append("Remote")
    return ", ".join(normalized)


JOB_SOURCES = {ArbeitnowSource.name: ArbeitnowSource}


def fetch_jobs(source_name: str = "arbeitnow", page: int = 1) -> List[Dict[str, Any]]:
    """Fetch jobs through an explicitly registered source adapter."""
    source_type = JOB_SOURCES.get(source_name)
    if source_type is None:
        raise ValueError(f"Unsupported job source: {source_name}")
    return source_type().fetch(page=page)
