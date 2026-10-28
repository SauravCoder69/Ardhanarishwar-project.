import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import database.database as database
from core.job_search import parse_job_search_query, validate_job_filters
from database import models
from database.reset_admin_password import reset_admin_password


class SecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "test.db"
        self.db_path_patch = patch.object(database, "DB_PATH", self.database_path)
        self.db_path_patch.start()
        database.init_db()
        self.candidate_a_id = models.create_user(
            "candidate_a", "candidate-pass-a", "Candidate", "tenant_a"
        )
        self.candidate_b_id = models.create_user(
            "candidate_b", "candidate-pass-b", "Candidate", "tenant_b"
        )
        self.admin_id = models.create_user(
            "admin_test", "administrator-pass", "Candidate", "tenant_admin"
        )
        connection = database.get_connection()
        connection.execute(
            "UPDATE users SET role = 'Admin', tenant_id = 'tenant_global' WHERE id = ?;",
            (self.admin_id,)
        )
        connection.commit()
        connection.close()

        self.candidate_a = {
            "id": self.candidate_a_id,
            "role": "Candidate",
            "tenant_id": "tenant_a",
        }
        self.candidate_b = {
            "id": self.candidate_b_id,
            "role": "Candidate",
            "tenant_id": "tenant_b",
        }
        self.admin = {
            "id": self.admin_id,
            "role": "Admin",
            "tenant_id": "tenant_global",
        }

    def tearDown(self):
        self.db_path_patch.stop()
        self.temp_dir.cleanup()

    def test_password_hashing_and_legacy_hash_upgrade(self):
        connection = database.get_connection()
        candidate_hash = connection.execute(
            "SELECT password_hash FROM users WHERE id = ?;", (self.candidate_a_id,)
        ).fetchone()["password_hash"]
        self.assertTrue(candidate_hash.startswith("$argon2id$"))
        self.assertIsNotNone(models.authenticate_user("candidate_a", "candidate-pass-a"))
        self.assertIsNone(models.authenticate_user("candidate_a", "wrong-password"))

        legacy_password = "legacy-pass"
        legacy_hash = hashlib.sha256(
            (legacy_password + "ardhanarishwar_salt_2026").encode("utf-8")
        ).hexdigest()
        connection.execute(
            "INSERT INTO users (username, password_hash, role, tenant_id) VALUES (?, ?, ?, ?);",
            ("legacy_candidate", legacy_hash, "Candidate", "tenant_legacy"),
        )
        connection.commit()
        connection.close()

        self.assertIsNotNone(models.authenticate_user("legacy_candidate", legacy_password))
        connection = database.get_connection()
        upgraded_hash = connection.execute(
            "SELECT password_hash FROM users WHERE username = 'legacy_candidate';"
        ).fetchone()["password_hash"]
        self.assertTrue(upgraded_hash.startswith("$argon2id$"))
        connection.close()

    def test_registration_does_not_seed_or_create_privileged_accounts(self):
        connection = database.get_connection()
        connection.execute("DELETE FROM users;")
        connection.commit()
        connection.close()
        self.assertIsNone(
            models.create_user("attempt_admin", "secure-password", "Admin", "tenant_admin")
        )
        database.init_db()
        connection = database.get_connection()
        self.assertEqual(connection.execute("SELECT COUNT(*) FROM users;").fetchone()[0], 0)
        connection.close()

    def test_local_admin_password_reset_updates_only_admin_credentials(self):
        with self.assertRaises(ValueError):
            reset_admin_password("admin_test", "short")
        with self.assertRaises(ValueError):
            reset_admin_password("candidate_a", "a-strong-password")

        reset_admin_password("admin_test", "a-strong-new-password")
        self.assertIsNone(models.authenticate_user("admin_test", "administrator-pass"))
        self.assertIsNotNone(models.authenticate_user("admin_test", "a-strong-new-password"))

    def test_feedback_and_admin_data_access_are_role_and_tenant_scoped(self):
        self.assertTrue(models.user_matches_tenant(self.candidate_a_id, "tenant_a", "Candidate"))
        self.assertFalse(models.user_matches_tenant(self.candidate_a_id, "tenant_b", "Candidate"))
        self.assertFalse(models.user_matches_tenant(self.candidate_a_id, "tenant_a", "Admin"))
        self.assertTrue(
            models.record_feedback(self.candidate_a, "career question", "answer", 1)
        )
        self.assertFalse(models.record_feedback(self.admin, "question", "answer", 1))

        with self.assertRaises(PermissionError):
            models.get_feedback_stats(self.candidate_a)
        with self.assertRaises(PermissionError):
            models.get_all_users(self.candidate_a)
        with self.assertRaises(PermissionError):
            models.get_job_applications(self.candidate_a)
        self.assertFalse(models.delete_user(self.candidate_a, self.candidate_b_id))

    def test_new_database_does_not_create_knowledge_base_or_unanswered_question_tables(self):
        connection = database.get_connection()
        tables = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table';"
            ).fetchall()
        }
        connection.close()
        self.assertNotIn("documents", tables)
        self.assertNotIn("unanswered_questions", tables)

    def test_user_deletion_cascades_owned_records_and_enforces_foreign_keys(self):
        models.save_candidate_profile(
            self.candidate_a_id, "Degree", "Python", "2 years", "Engineer", "Engineer", "AI"
        )
        conversation_id = models.create_conversation(
            self.candidate_a_id, "tenant_a", "Candidate", "Test chat"
        )
        models.save_message(conversation_id, "user", "question")
        models.save_resume_analysis(self.candidate_a_id, "resume.pdf", 80, "Engineer", 75, "Python")
        models.record_feedback(self.candidate_a, "question", "answer", 1)

        connection = database.get_connection()
        cursor = connection.execute("""
        INSERT INTO jobs (business_id, tenant_id, company_name, title, description, required_skills, experience, location, job_type, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending Approval');
        """, (
            self.admin_id, "tenant_admin", "Example Co", "Engineer", "Description",
            "Python", "2 years", "Remote", "Full-time"
        ))
        job_id = cursor.lastrowid
        connection.commit()
        connection.close()
        self.assertTrue(models.update_job_status(self.admin, job_id, "Approved"))
        self.assertTrue(models.apply_to_job(job_id, self.candidate_a, "resume.pdf", "Interested"))
        self.assertFalse(models.apply_to_job(job_id, self.admin, "resume.pdf", "Not allowed"))

        connection = database.get_connection()
        self.assertEqual(connection.execute("PRAGMA foreign_keys;").fetchone()[0], 1)
        connection.close()
        self.assertTrue(models.delete_user(self.admin, self.candidate_a_id))

        connection = database.get_connection()
        for table in (
            "candidate_profiles",
            "conversations",
            "messages",
            "resume_analyses",
            "feedback",
            "job_applications",
        ):
            self.assertEqual(connection.execute(f"SELECT COUNT(*) FROM {table};").fetchone()[0], 0)
        self.assertEqual(connection.execute("PRAGMA foreign_key_check;").fetchall(), [])
        connection.close()

    def test_aggregated_job_deduplication_and_candidate_ownership(self):
        listing = {
            "source": "test_source",
            "source_id": "job-1",
            "company_name": "Example Co",
            "title": "Python Engineer",
            "description": "Build software",
            "required_skills": "Python, SQL",
            "experience": "Entry-level",
            "salary": "",
            "location": "Remote",
            "job_type": "Full-time",
            "job_url": "https://jobs.example/job-1",
            "remote": True,
            "posted_at": "2026-01-01",
        }
        models.upsert_aggregated_jobs([listing])
        models.upsert_aggregated_jobs([{**listing, "title": "Senior Python Engineer"}])
        self.assertEqual(models.search_aggregated_jobs(role="Senior", location="remote"), [])

        pending = models.get_aggregated_jobs_for_review(self.admin)
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["review_status"], "Pending Review")
        self.assertFalse(models.save_aggregated_job(self.candidate_a, pending[0]["id"]))
        with self.assertRaises(PermissionError):
            models.get_aggregated_jobs_for_review(self.candidate_a)
        self.assertFalse(models.update_aggregated_job_status(self.candidate_a, pending[0]["id"], "Approved"))
        self.assertFalse(models.update_aggregated_job_status(self.admin, pending[0]["id"], "Unknown"))
        self.assertTrue(
            models.update_aggregated_job_status(self.admin, pending[0]["id"], "Approved", "Verified source")
        )

        models.upsert_aggregated_jobs([{**listing, "title": "Senior Python Engineer updated"}])
        jobs = models.search_aggregated_jobs(role="Senior", location="remote")
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["title"], "Senior Python Engineer updated")
        self.assertEqual(jobs[0]["review_status"], "Approved")
        self.assertEqual(jobs[0]["admin_note"], "Verified source")
        self.assertEqual(len(models.search_aggregated_jobs(query="Example Co")), 1)
        self.assertEqual(len(models.search_aggregated_jobs(query="Build software")), 1)
        self.assertTrue(models.save_aggregated_job(self.candidate_a, jobs[0]["id"]))
        self.assertEqual(models.get_tracked_applications(self.candidate_b), [])
        self.assertFalse(
            models.update_tracked_application(self.candidate_b, jobs[0]["id"], "Applied")
        )
        self.assertTrue(
            models.update_tracked_application(self.candidate_a, jobs[0]["id"], "Applied")
        )
        self.assertTrue(models.update_aggregated_job_status(self.admin, jobs[0]["id"], "Rejected"))
        self.assertEqual(models.search_aggregated_jobs(role="Senior", location="remote"), [])
        self.assertEqual(models.get_tracked_applications(self.candidate_a), [])

    def test_existing_aggregated_jobs_require_review_after_schema_migration(self):
        connection = database.get_connection()
        connection.execute("DROP TABLE tracked_applications;")
        connection.execute("DROP TABLE saved_jobs;")
        connection.execute("DROP TABLE aggregated_jobs;")
        connection.execute("""
        CREATE TABLE aggregated_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            source_id TEXT NOT NULL,
            company_name TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            required_skills TEXT,
            experience TEXT,
            salary TEXT,
            location TEXT,
            job_type TEXT,
            job_url TEXT NOT NULL,
            remote INTEGER NOT NULL DEFAULT 0,
            posted_at TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source, source_id),
            UNIQUE(source, job_url)
        );
        """)
        connection.execute("""
        INSERT INTO aggregated_jobs (
            source, source_id, company_name, title, description, job_url
        ) VALUES ('legacy_source', 'legacy-1', 'Example Co', 'Engineer', 'Role description',
                  'https://jobs.example/legacy-1');
        """)
        connection.commit()
        connection.close()

        database.init_db()

        listings = models.get_aggregated_jobs_for_review(self.admin)
        self.assertEqual(len(listings), 1)
        self.assertEqual(listings[0]["review_status"], "Pending Review")
        self.assertEqual(models.search_aggregated_jobs(), [])

    def test_job_search_copilot_filters_are_validated(self):
        response = (
            '{"role":"Python engineer","location":"Berlin","skills":["Python","Django"],'
            '"experience":"Entry-level","job_type":"Remote"}'
        )
        with patch("core.job_search.llm_client.generate", return_value=response):
            filters = parse_job_search_query("remote junior Python jobs in Berlin")
        self.assertEqual(filters["role"], "Python engineer")
        self.assertEqual(filters["skills"], ["Python", "Django"])
        self.assertEqual(filters["job_type"], "Remote")
        with self.assertRaises(ValueError):
            validate_job_filters({"job_type": "Unknown"})
        with self.assertRaises(ValueError):
            validate_job_filters({"skills": "Python"})


if __name__ == "__main__":
    unittest.main()
