import unittest
from unittest.mock import patch

from modules.interview import (
    _build_evaluation_prompt,
    _generate_questions,
    _parse_evaluation,
    _parse_questions,
)


class InterviewTests(unittest.TestCase):
    def test_questions_are_generated_from_resume_and_job_description(self):
        response = "1. How did you use Python?\n2. How would you build the API?\n3. Tell me about your deployment project."
        with patch("modules.interview.llm_client.generate", return_value=response) as generate:
            questions = _generate_questions(
                "Backend Developer",
                "Junior",
                "Medium",
                "Technical & Coding",
                "Resume includes Python and a Django project.",
                "Role requires Python, Django, REST APIs, and deployment.",
            )

        self.assertEqual(len(questions), 3)
        prompt = generate.call_args.args[0]
        self.assertIn("Resume includes Python and a Django project.", prompt)
        self.assertIn("Role requires Python, Django, REST APIs, and deployment.", prompt)

    def test_question_generation_rejects_malformed_output(self):
        with self.assertRaisesRegex(ValueError, "exactly three"):
            _parse_questions("Here are some ideas, but no numbered questions.")

    def test_answer_evaluation_uses_uploaded_context(self):
        prompt = _build_evaluation_prompt(
            "Describe your API project.",
            "I built a Django API.",
            "Resume: Django and Python project.",
            "JD: Build REST APIs with Django.",
        )
        self.assertIn("Resume: Django and Python project.", prompt)
        self.assertIn("JD: Build REST APIs with Django.", prompt)

    def test_evaluation_parses_ai_scores_and_feedback(self):
        evaluation, overall, technical, communication = _parse_evaluation(
            '{"technical_accuracy": 80, "job_relevance": 90, '
            '"communication": 70, "feedback": "Add more implementation detail."}'
        )
        self.assertEqual(evaluation["feedback"], "Add more implementation detail.")
        self.assertEqual(technical, 85)
        self.assertEqual(communication, 70)
        self.assertEqual(overall, 80.5)

    def test_evaluation_rejects_invalid_scores(self):
        with self.assertRaisesRegex(ValueError, "invalid evaluation scores"):
            _parse_evaluation(
                '{"technical_accuracy": 120, "job_relevance": 90, '
                '"communication": 70, "feedback": "Invalid score."}'
            )


if __name__ == "__main__":
    unittest.main()
