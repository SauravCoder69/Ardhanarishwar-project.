from typing import Any, Dict

import streamlit as st

from database.models import (
    get_tracked_applications,
    save_aggregated_job,
    search_aggregated_jobs,
    update_tracked_application,
    upsert_aggregated_jobs,
)
from modules.job_sources import fetch_jobs
from utils.helpers import render_header


def refresh_job_listings(source_name: str = "arbeitnow") -> int:
    """Fetch a permitted source and persist its normalized listings."""
    new_jobs = fetch_jobs(source_name)
    upsert_aggregated_jobs(new_jobs)
    return len(new_jobs)


def render_job_search(current_user: Dict[str, Any]):
    """Render approved external listings with simple candidate-side search."""
    if current_user.get("role") != "Candidate":
        st.error("Job search is available to candidate accounts only.")
        return

    render_header("Find Jobs")
    st.caption(
        "Browse jobs approved by the admin. Apply on the employer's website, then track your progress in My Applications."
    )
    col_search, col_type = st.columns([3, 1])
    query = col_search.text_input(
        "Search approved jobs",
        placeholder="Job title, company, skill, location, or source",
        key="approved_job_search",
    )
    job_type = col_type.selectbox(
        "Job type",
        ["All", "Full-time", "Part-time", "Contract", "Internship", "Temporary", "Remote"],
        key="approved_job_type",
    )
    jobs = search_aggregated_jobs(
        query=query,
        job_type="" if job_type == "All" else job_type,
    )

    if not jobs:
        st.info("No approved jobs match your search. Try another keyword or check back after the admin reviews new listings.")
        return

    tracked = {item["job_id"]: item for item in get_tracked_applications(current_user)}
    st.caption(f"{len(jobs)} approved listing(s)")
    for job in jobs:
        with st.container(border=True):
            st.subheader(job["title"])
            st.write(f"**{job['company_name']}** · {job['location'] or 'Location not specified'}")
            st.caption(
                f"Source: {job['source']} · Type: {job['job_type'] or 'Not specified'} · "
                f"Skills: {job['required_skills'] or 'Not specified'}"
            )
            st.write(job["description"][:700] or "No description provided.")
            col_save, col_open = st.columns(2)
            if job["id"] not in tracked:
                if col_save.button("Track this job", key=f"save_job_{job['id']}"):
                    if save_aggregated_job(current_user, job["id"]):
                        st.success("Added to My Applications. This does not submit an application.")
                    else:
                        st.error("Could not save this job.")
                    st.rerun()
            else:
                col_save.caption(f"Your status: {tracked[job['id']]['status']}")
            col_open.link_button("View listing & apply on employer site", job["job_url"])


def render_my_applications(current_user: Dict[str, Any]):
    """Render the authenticated candidate's saved jobs and self-reported statuses."""
    if current_user.get("role") != "Candidate":
        st.error("Applications are available to candidate accounts only.")
        return

    render_header("My Applications")
    st.caption(
        "This is your personal tracker, not an application submitted to the employer. "
        "Open the employer listing to apply, then update your status here."
    )
    applications = get_tracked_applications(current_user)
    if not applications:
        st.info("No jobs tracked yet. Find an approved job and select **Track this job**.")
        return

    statuses = ["Saved", "Applied", "Interview", "Offer", "Rejected", "Closed"]
    status_labels = {
        "Saved": "Saved — not applied yet",
        "Applied": "Applied — on employer website",
        "Interview": "Interview",
        "Offer": "Offer",
        "Rejected": "Rejected",
        "Closed": "Closed",
    }
    for application in applications:
        with st.container(border=True):
            st.subheader(application["title"])
            st.write(
                f"**{application['company_name']}** · {application['location'] or 'Location not specified'}"
            )
            st.caption(
                f"Source: {application['source']} · "
                f"Your status: {status_labels.get(application['status'], application['status'])}"
            )
            st.link_button("Open employer listing", application["job_url"])
            selected = st.selectbox(
                "Update your status",
                statuses,
                index=statuses.index(application["status"]) if application["status"] in statuses else 0,
                format_func=status_labels.get,
                key=f"application_status_{application['job_id']}",
            )
            if selected != application["status"] and st.button(
                "Save status", key=f"save_application_status_{application['job_id']}"
            ):
                if update_tracked_application(current_user, application["job_id"], selected):
                    st.success("Application status updated.")
                    st.rerun()
                st.error("Could not update this application's status.")
