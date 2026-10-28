import streamlit as st
import requests
from database.models import get_aggregated_jobs_for_review, update_aggregated_job_status
from utils.helpers import render_header
from modules.job_aggregator import refresh_job_listings


def _job_details(job):
    st.markdown(f"### {job['title']}")
    st.write(f"**Company:** {job['company_name']}")
    st.write(f"**Location:** {job['location'] or 'Not specified'} | **Job type:** {job['job_type'] or 'Not specified'}")
    st.write(f"**Experience:** {job['experience'] or 'Not specified'} | **Salary:** {job['salary'] or 'Not specified'}")
    st.write(f"**Required skills:** {job['required_skills'] or 'Not specified'}")
    st.markdown("**Job description**")
    st.write(job['description'])


def render_admin_job_portal(current_user):
    """Render the admin review queue for external job listings."""
    if not current_user or current_user.get("role") != "Admin":
        st.error("Only administrators can review external job listings.")
        return
    render_header("Job Management")
    st.caption("Refresh job sources here. Candidates can see only listings you approve.")
    st.markdown("### External Listings")
    if st.button("Refresh listings from Arbeitnow", key="admin_refresh_external_jobs"):
        try:
            with st.spinner("Fetching listings from Arbeitnow..."):
                refreshed_count = refresh_job_listings("arbeitnow")
        except (requests.RequestException, ValueError) as exc:
            st.error(f"Could not refresh external listings: {exc}")
        else:
            st.success(f"Fetched and normalized {refreshed_count} listings.")

    external_jobs = get_aggregated_jobs_for_review(current_user)
    if external_jobs:
        for job in external_jobs:
            with st.expander(
                f"{job['title']} | {job['company_name']} | "
                f"{job['source']} | {job['review_status']}"
            ):
                _job_details(job)
                st.caption(f"Source: {job['source']} · Posted: {job['posted_at'] or 'Not specified'}")
                st.link_button("Open original listing", job["job_url"])
                note = st.text_input(
                    "Admin Note",
                    value=job["admin_note"] or "",
                    key=f"external_job_note_{job['id']}",
                )
                col1, col2, col3 = st.columns(3)
                for column, label, status in (
                    (col1, "✅ Approve", "Approved"),
                    (col2, "❌ Reject", "Rejected"),
                    (col3, "⏸️ Close", "Closed"),
                ):
                    status_key = status.lower().replace(" ", "_")
                    if column.button(label, key=f"external_job_{status_key}_{job['id']}"):
                        if update_aggregated_job_status(current_user, job["id"], status, note):
                            st.rerun()
                        st.error("Could not update external listing review status.")
    else:
        st.info("No listings are available yet. Use Refresh listings to fetch jobs from connected sources.")
