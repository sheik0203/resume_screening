import re

import pymupdf as fitz
from django.conf import settings
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


SKILL_VOCABULARY = (
    "Python",
    "Django",
    "Flask",
    "JavaScript",
    "React",
    "SQL",
    "PostgreSQL",
    "REST APIs",
    "Docker",
    "Git",
    "machine learning",
    "NLP",
)


class ResumeExtractionError(ValueError):
    """A resume could not be safely read as a text-based PDF."""


def preprocess_text(text):
    return re.sub(r"\s+", " ", text or "").strip()


def extract_pdf_text(uploaded_file):
    """Extract text from an in-memory PDF without saving it to application storage."""
    try:
        pdf_bytes = uploaded_file.read()
        uploaded_file.seek(0)
        document = fitz.open(stream=pdf_bytes, filetype="pdf")
    except (
        fitz.FileDataError,
        fitz.FileNotFoundError,
        OSError,
        RuntimeError,
        ValueError,
    ) as exc:
        raise ResumeExtractionError(
            "This file is not a valid or readable PDF. Please upload an uncorrupted PDF."
        ) from exc

    try:
        if document.needs_pass:
            raise ResumeExtractionError(
                "This PDF is password-protected. Upload an unlocked PDF."
            )
        if len(document) > settings.MAX_RESUME_PAGES:
            raise ResumeExtractionError(
                "This PDF has too many pages. Upload a document with no more than "
                f"{settings.MAX_RESUME_PAGES} pages."
            )
        text = preprocess_text("\n".join(page.get_text() for page in document))
    except ResumeExtractionError:
        raise
    except (fitz.FileDataError, OSError, RuntimeError, ValueError) as exc:
        raise ResumeExtractionError(
            "Text could not be extracted from this PDF. Please try a different file."
        ) from exc
    finally:
        document.close()

    if not text:
        raise ResumeExtractionError(
            "No extractable text was found. This PDF may be scanned; use a text-based PDF."
        )
    return text


def extract_skills(text):
    normalized_text = preprocess_text(text).casefold()
    found = []
    for skill in SKILL_VOCABULARY:
        pattern = rf"(?<!\w){re.escape(skill.casefold())}(?!\w)"
        if re.search(pattern, normalized_text):
            found.append(skill)
    return found


def rank_resumes(job_description, candidates):
    """Return candidates ranked by TF-IDF cosine similarity and job-specific skills."""
    job_text = preprocess_text(job_description)
    if not job_text:
        raise ValueError("A non-empty job description is required.")
    if not candidates:
        return []

    candidate_texts = [preprocess_text(candidate["text"]) for candidate in candidates]
    if any(not text for text in candidate_texts):
        raise ValueError("Candidate resume text cannot be empty.")

    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 2),
    )
    try:
        vectors = vectorizer.fit_transform([job_text, *candidate_texts])
    except ValueError as exc:
        raise ValueError(
            "The job description and resumes must contain readable words to compare."
        ) from exc

    similarities = cosine_similarity(vectors[0:1], vectors[1:]).ravel()
    required_skills = extract_skills(job_text)
    ranked = []
    for candidate, text, similarity in zip(candidates, candidate_texts, similarities):
        candidate_skills = set(extract_skills(text))
        matched_skills = [
            skill for skill in required_skills if skill in candidate_skills
        ]
        missing_skills = [
            skill for skill in required_skills if skill not in candidate_skills
        ]
        ranked.append(
            {
                "filename": candidate["filename"],
                "score": round(float(similarity) * 100, 1),
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
            }
        )

    return sorted(
        ranked,
        key=lambda result: (-result["score"], result["filename"].casefold()),
    )
