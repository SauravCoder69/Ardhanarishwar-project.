# Ardhanarishwar AI

Ardhanarishwar is a Streamlit AI job aggregator and career assistant. Candidate navigation is limited to **Dashboard**, **Find Jobs**, **My Applications**, and **My Profile**. Account, job-listing, and analytics administration is available separately to authorized administrators.

## Candidate features

- Search administrator-approved job listings by keyword and job type.
- Admins refresh listings from Arbeitnow's public Job Board API (`https://www.arbeitnow.com/api/job-board-api`). The integration uses the API, not website scraping, and is isolated behind a source adapter.
- External listings are hidden from candidates until an administrator approves them in **Job Management → External Listings**. Rejected and closed listings remain hidden; refreshes preserve the admin decision.
- Normalize and deduplicate cached job records by source identity and URL.
- Candidates apply on the employer's website, then optionally track the job and self-report their progress in **My Applications**. The app does not receive external applications or expose candidate application statuses to admins.
- Interview practice accepts a resume and job description (PDF, DOCX, or TXT) and uses both to generate questions and evaluate answers. Uploaded files are not saved by the app.
- Use the retained LangGraph career assistant, ATS resume analysis, resume-to-JD matching, skill-gap analysis, career counselling, learning roadmaps, and mock interview practice under **My Profile**.

Only the first API page is fetched per refresh. Availability, rate limits, job details, and apply workflows are controlled by the external provider and should be checked on the original listing.

## Architecture

- **UI:** Streamlit
- **Agent routing:** LangGraph `StateGraph` with Resume, Interview, Career, and General Assistant routes
- **LLM:** Local Ollama
- **Database:** SQLite; existing user records and legacy internal jobs/applications are retained
- **Authentication:** Argon2id. Existing SHA-256 password hashes are verified and upgraded to Argon2id at the next successful login.

## Setup

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

The app applies additive SQLite schema updates at startup. SQLite foreign-key enforcement is enabled for every connection. No demo users or default administrator credentials are created.

### Provision an administrator

Create an administrator from the project directory in a trusted terminal. Enter the display name and a unique password when prompted; password input is hidden, and only its Argon2id hash is stored:

```bash
python -m database.create_admin AnkitJha
```

Choose any unused username in place of `AnkitJha`. The command asks for the admin's full name and a password of at least 12 characters. It creates a new Admin account; it does not change an existing account's password. Existing non-default administrator accounts remain available and their legacy password hashes are upgraded on successful authentication. The previously documented default password for the existing `admin` account has been revoked; reset that account locally before using the Admin UI. Existing Business accounts and data are retained, but Business workspaces are no longer available in the candidate-focused UI.

Reset an existing administrator password from a trusted terminal. This prompts without echo, requires at least 12 characters, and stores only an Argon2id hash:

```bash
python -m database.reset_admin_password admin
```

Any previously shared or publicly documented administrator password should be revoked and reset before deployment.

## Security and data handling

- Candidate feedback is limited to candidate accounts; administrators can see aggregate feedback.
- Job applications and saved listings are tied to the candidate account. Administrator application management checks the administrator role.
- User deletion cascades through user-owned profiles, conversations/messages, interviews, resume analyses, feedback, jobs, and applications where applicable.
- Legacy orphaned profile and feedback records are retained but detached from nonexistent user IDs during migration.
- Interview practice extracts text from the candidate's uploaded resume and job description and sends that text to the configured Ollama model for the session. The app does not save those files or extracted text.
- Existing knowledge-base metadata and Qdrant files from older versions are not automatically deleted, but the application no longer creates or reads them.

## Tests

Run the focused security and data-integrity suite:

```bash
python -m unittest discover -s tests -v
```
