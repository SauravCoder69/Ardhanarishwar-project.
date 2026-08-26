import streamlit as st
from pathlib import Path
import uuid
from database.models import (
    apply_to_job,
    create_job,
    get_candidate_applications,
    get_job_applications,
    get_jobs,
    has_applied,
    update_job_status,
)
from utils.helpers import render_header


def _job_details(job):
    st.markdown(f"### {job['title']}")
    st.write(f"**Company:** {job['company_name']}")
    st.write(f"**Location:** {job['location'] or 'Not specified'} | **Job type:** {job['job_type'] or 'Not specified'}")
    st.write(f"**Experience:** {job['experience'] or 'Not specified'} | **Salary:** {job['salary'] or 'Not specified'}")
    st.write(f"**Required skills:** {job['required_skills'] or 'Not specified'}")
    st.markdown("**Job description**")
    st.write(job['description'])


def _resume_download(application, key: str):
    """Show a resume download control when an uploaded file exists."""
    resume_path = application.get('resume_path')
    if resume_path and Path(resume_path).is_file():
        st.download_button(
            "⬇️ Download Resume",
            data=Path(resume_path).read_bytes(),
            file_name=application['resume_name'],
            key=key
        )


def render_business_job_portal(user_id: int, tenant_id: str):
    """Render Business job posting and application review."""
    render_header("Business Job Portal")
    st.markdown("### 📢 Post a Job for Candidate Applications")
    st.info("New jobs go to Admin for approval. Candidates see them only after approval.")

    with st.form("post_job_form"):
        col1, col2 = st.columns(2)
        with col1:
            company_name = st.text_input("Company Name")
            title = st.text_input("Job Title", placeholder="e.g. Python Developer")
            location = st.text_input("Location", placeholder="e.g. Delhi / Remote")
            job_type = st.selectbox("Job Type", ["Full-time", "Part-time", "Contract", "Internship", "Remote"])
        with col2:
            experience = st.text_input("Experience Required", placeholder="e.g. 0-2 years")
            salary = st.text_input("Salary Range", placeholder="e.g. Rs. 4-7 LPA")
            required_skills = st.text_input("Required Skills", placeholder="e.g. Python, SQL, FastAPI")
        description = st.text_area("Full Job Description", height=180)
        submitted = st.form_submit_button("📤 Submit Job for Admin Approval", type="primary")

    if submitted:
        fields = [company_name, title, description, required_skills, experience, salary, location]
        if not all(field.strip() for field in fields):
            st.warning("Please complete all job details before submitting.")
        else:
            create_job(user_id, tenant_id, company_name, title, description, required_skills, experience, salary, location, job_type)
            st.success("Job submitted. It will appear to candidates after Admin approval.")

    st.markdown("---")
    st.markdown("### 📋 Your Job Posts")
    jobs = get_jobs(business_id=user_id)
    if jobs:
        for job in jobs:
            with st.expander(f"{job['title']} | {job['company_name']} | {job['status']}"):
                _job_details(job)
                if job['admin_note']:
                    st.caption(f"Admin note: {job['admin_note']}")
    else:
        st.info("You have not posted any jobs yet.")

    st.markdown("### 👥 Applications Received")
    applications = get_job_applications(business_id=user_id)
    if applications:
        for application in applications:
            st.write(
                f"**{application['full_name']}** ({application['email'] or application['username']}) "
                f"applied for **{application['title']}** on {application['applied_at']}"
            )
            st.caption(f"Resume: {application['resume_name'] or 'Not provided'} | Message: {application['cover_message'] or 'None'}")
            _resume_download(application, f"business_resume_{application['id']}")
    else:
        st.info("No applications received yet.")


def render_admin_job_portal():
    """Render Admin job approval and application oversight."""
    render_header("Admin Job Management")
    st.markdown("### 🛡️ Review Job Posts")
    jobs = get_jobs()
    if jobs:
        for job in jobs:
            with st.expander(f"{job['title']} | {job['company_name']} | {job['status']}"):
                _job_details(job)
                note = st.text_input("Admin Note", value=job['admin_note'] or "", key=f"job_note_{job['id']}")
                col1, col2, col3 = st.columns(3)
                if col1.button("✅ Approve", key=f"approve_job_{job['id']}"):
                    update_job_status(job['id'], "Approved", note)
                    st.rerun()
                if col2.button("❌ Reject", key=f"reject_job_{job['id']}"):
                    update_job_status(job['id'], "Rejected", note)
                    st.rerun()
                if col3.button("⏸️ Close", key=f"close_job_{job['id']}"):
                    update_job_status(job['id'], "Closed", note)
                    st.rerun()
    else:
        st.info("No job posts are available for review.")

    st.markdown("### 📥 All Candidate Applications")
    applications = get_job_applications()
    if applications:
        for application in applications:
            st.write(
                f"**{application['full_name']}** ({application['email'] or application['username']}) "
                f"→ **{application['title']}** at {application['company_name']} | "
                f"Status: {application['status']} | {application['applied_at']}"
            )
            _resume_download(application, f"admin_resume_{application['id']}")
    else:
        st.info("No candidate applications yet.")


def render_candidate_job_portal(candidate_id: int):
    """Render approved jobs and candidate Apply Now workflow."""
    render_header("Job Portal")
    st.markdown("### 🔎 Find Your Next Opportunity")
    st.info("Browse Admin-approved jobs, open every detail, and apply directly.")

    jobs = get_jobs(status="Approved")
    search = st.text_input("Search jobs", placeholder="Title, company, skill, or location")
    job_type_filter = st.selectbox("Filter by Job Type", ["All", "Full-time", "Part-time", "Contract", "Internship", "Remote"])
    search_lower = search.strip().lower()
    filtered_jobs = [
        job for job in jobs
        if (not search_lower or search_lower in f"{job['title']} {job['company_name']} {job['required_skills']} {job['location']}".lower())
        and (job_type_filter == "All" or job['job_type'] == job_type_filter)
    ]

    if filtered_jobs:
        for job in filtered_jobs:
            with st.expander(f"{job['title']} | {job['company_name']} | {job['location']}"):
                _job_details(job)
                if has_applied(job['id'], candidate_id):
                    st.success("You have already applied to this job.")
                else:
                    with st.form(f"apply_job_form_{job['id']}"):
                        resume_file = st.file_uploader(
                            "Upload Resume",
                            type=["pdf", "docx", "txt"],
                            key=f"resume_upload_{job['id']}"
                        )
                        cover_message = st.text_area("Short application message", height=100)
                        apply_clicked = st.form_submit_button("🚀 Apply Now", type="primary")
                    if apply_clicked:
                        if not resume_file:
                            st.warning("Please upload your resume before applying.")
                        else:
                            resume_dir = Path(__file__).resolve().parent.parent / "data" / "job_resumes"
                            resume_dir.mkdir(parents=True, exist_ok=True)
                            stored_name = f"{uuid.uuid4().hex}_{Path(resume_file.name).name}"
                            resume_path = resume_dir / stored_name
                            resume_path.write_bytes(resume_file.getvalue())
                            if apply_to_job(job['id'], candidate_id, resume_file.name, cover_message, str(resume_path)):
                                st.success("Application and resume submitted successfully.")
                                st.rerun()
                            else:
                                resume_path.unlink(missing_ok=True)
                                st.warning("You have already applied to this job.")
    else:
        st.info("No approved jobs match your search right now.")

    st.markdown("---")
    st.markdown("### 📄 My Applications")
    applications = get_candidate_applications(candidate_id)
    if applications:
        for application in applications:
            st.write(
                f"**{application['title']}** at {application['company_name']} | "
                f"{application['location'] or 'Location not specified'} | "
                f"{application['status']} | Applied: {application['applied_at']}"
            )
    else:
        st.info("You have not applied to any jobs yet.")
