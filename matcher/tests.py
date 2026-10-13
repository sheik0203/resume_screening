import pymupdf as fitz
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from .forms import ResumeScreeningForm
from .services import (
    ResumeExtractionError,
    extract_pdf_text,
    extract_skills,
    rank_resumes,
)


def make_pdf(text):
    document = fitz.open()
    page = document.new_page()
    if text:
        page.insert_text((72, 72), text)
    content = document.tobytes()
    document.close()
    return content


class ResumeServiceTests(TestCase):
    def test_extracts_text_from_valid_pdf(self):
        uploaded_file = SimpleUploadedFile(
            "resume.pdf", make_pdf("Python developer with Django experience")
        )
        self.assertIn("Python developer", extract_pdf_text(uploaded_file))

    def test_rejects_invalid_pdf(self):
        uploaded_file = SimpleUploadedFile("broken.pdf", b"not a PDF")
        with self.assertRaisesRegex(ResumeExtractionError, "valid or readable PDF"):
            extract_pdf_text(uploaded_file)

    def test_rejects_empty_pdf(self):
        uploaded_file = SimpleUploadedFile("empty.pdf", make_pdf(""))
        with self.assertRaisesRegex(ResumeExtractionError, "No extractable text"):
            extract_pdf_text(uploaded_file)

    def test_matching_score_is_bounded(self):
        results = rank_resumes(
            "Python Django developer",
            [{"filename": "candidate.pdf", "text": "Python developer"}],
        )
        self.assertGreaterEqual(results[0]["score"], 0)
        self.assertLessEqual(results[0]["score"], 100)

    def test_extracts_configured_skills_case_insensitively(self):
        self.assertEqual(
            extract_skills("Django, PostgreSQL, REST APIs and machine learning"),
            ["Django", "PostgreSQL", "REST APIs", "machine learning"],
        )

    def test_ranks_candidates_by_descending_similarity(self):
        results = rank_resumes(
            "Python Django developer",
            [
                {"filename": "other.pdf", "text": "Chef and pastry specialist"},
                {"filename": "match.pdf", "text": "Python Django developer"},
            ],
        )
        self.assertEqual(results[0]["filename"], "match.pdf")
        self.assertEqual(
            [result["score"] for result in results],
            sorted(
                (result["score"] for result in results),
                reverse=True,
            ),
        )

    def test_identical_scores_have_deterministic_filename_order(self):
        results = rank_resumes(
            "Python developer",
            [
                {"filename": "zeta.pdf", "text": "Python developer"},
                {"filename": "Alpha.pdf", "text": "Python developer"},
            ],
        )
        self.assertEqual([item["filename"] for item in results], ["Alpha.pdf", "zeta.pdf"])


class ResumeScreeningViewTests(TestCase):
    def test_upload_page_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Analyze resumes")

    def test_invalid_upload_shows_understandable_error(self):
        response = self.client.post(
            "/",
            {
                "job_description": "Python developer",
                "resumes": SimpleUploadedFile("resume.txt", b"not a PDF"),
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "only PDF files are accepted", status_code=400)

    def test_corrupt_pdf_upload_shows_understandable_error(self):
        response = self.client.post(
            "/",
            {
                "job_description": "Python developer",
                "resumes": SimpleUploadedFile("broken.pdf", b"not a PDF"),
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertContains(
            response,
            "not a valid or readable PDF",
            status_code=400,
        )

    def test_missing_job_description_shows_validation_error(self):
        response = self.client.post(
            "/",
            {"resumes": SimpleUploadedFile("resume.pdf", make_pdf("Python developer"))},
        )
        self.assertEqual(response.status_code, 400)
        self.assertContains(
            response,
            "Enter a job description",
            status_code=400,
        )

    def test_successful_submission_renders_ranked_results(self):
        response = self.client.post(
            "/",
            {
                "job_description": "Python Django developer",
                "resumes": [
                    SimpleUploadedFile(
                        "strong.pdf", make_pdf("Python Django developer")
                    ),
                    SimpleUploadedFile(
                        "weak.pdf", make_pdf("Chef and pastry specialist")
                    ),
                ],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "strong.pdf")
        self.assertContains(response, "weak.pdf")
        self.assertContains(response, "text-similarity estimate")
