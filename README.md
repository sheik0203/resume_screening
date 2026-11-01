# Job Matching Pro

A Django web application that compares PDF resumes with a job description, identifies relevant skills, and ranks candidates using TF-IDF and cosine similarity. Matching runs locally without an external AI API or paid service.

## Features

- Upload up to 10 PDF resumes at once.
- Extract text from PDFs with PyMuPDF.
- Explain errors for invalid, corrupt, password-protected, and text-empty PDFs.
- Compare job descriptions and resumes with TF-IDF and cosine similarity.
- Show a text-similarity score and the recognized required skills found or missing in each resume.
- Rank candidates from highest to lowest similarity.
- Display a responsive Django-template dashboard styled with Bootstrap.
- Process resumes for the current request without saving them as permanent resume records.

## Technology

- Python and Django
- PyMuPDF (`pymupdf`) for PDF extraction
- Scikit-learn (`TfidfVectorizer` and `cosine_similarity`) for matching
- HTML, CSS, Bootstrap 5, and JavaScript
- SQLite

## Requirements

- Python 3.10 or later
- pip

## Setup and run (PowerShell)

Open PowerShell in the project folder containing `manage.py`, then run:

```powershell
cd "C:\Users\Sheik abdullah\OneDrive\Desktop\Job_matching_system"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 127.0.0.1:8010
```

Open [http://127.0.0.1:8010/](http://127.0.0.1:8010/) in your browser. Leave the PowerShell window running while using the app. Stop the server with **Ctrl+C**.

If `.venv` already exists, you do not need to create it again; activate it and continue with dependency installation. If PowerShell blocks environment activation, run the project commands with the virtual environment's interpreter directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8010
```

If port 8010 is already in use, stop the other server or select another available port, such as `8000`.

## Try the included candidate resumes

Use this job description for the sample screening:

> We are looking for a junior Python developer with Django experience who can build REST APIs and work with PostgreSQL and SQL. Candidates should use Git and Docker. Experience with JavaScript, React, machine learning, or NLP is a plus.

In the application, select these three candidate resumes from `sample_resumes`:

- `01_high_match_software_developer.pdf` — Alex Morgan, a junior Python/Django developer with REST API and PostgreSQL project experience.
- `02_medium_match_frontend_developer.pdf` — Jamie Park, a frontend-focused developer with JavaScript, React, API integration, SQL, and Python experience.
- `03_low_match_data_analyst.pdf` — Taylor Reed, a data analyst whose resume focuses on reporting and visualization rather than web development.

With the example description, the intended relevance order is **Alex Morgan, Jamie Park, then Taylor Reed**. Exact scores depend on the submitted wording and the matching implementation; the percentage represents text similarity, not candidate suitability.

The folder also contains `empty_text_test.pdf` and `invalid_pdf_test.pdf`. These are validation fixtures, not candidate resumes. Upload them separately when testing the empty-text and invalid-PDF error messages.

## Upload limits and privacy

- PDF files only; maximum 10 resumes per submission.
- Maximum file size is 5 MB per file.
- Password-protected and corrupt PDFs are rejected with an explanation.
- Image-only scanned PDFs have no extractable text; OCR is not performed.
- PDFs are processed for the current request and are not stored as permanent resume records or media files. Django may temporarily spool larger incoming requests while handling uploads.
- The application extracts and compares text; it does not execute uploaded content.

## Matching approach and limitations

The application normalizes whitespace, builds TF-IDF features using unigrams and bigrams, and compares each resume with the job description using cosine similarity. Recognized skills come from the configurable vocabulary in `matcher/services.py`. The application reports skills recognized in the job description and indicates which of those are detected in each resume.

The matching percentage is a **text-similarity estimate, not a guarantee of candidate suitability**. It is not a hiring decision or a measure of qualifications. Similarity is sensitive to document wording. The application does not infer synonyms, judge the quality of experience, perform OCR, or call an external AI model. Review resumes in context.

## Tests and Django configuration check

Run these from the project root with the virtual environment activated:

```powershell
python manage.py test
python manage.py check
```

The Django tests cover PDF text extraction, invalid and empty PDFs, score bounds, skill extraction, candidate ranking, form validation, and resume submission.

## Production deployment

The Django development server is for local use only. Before deployment, set a private `DJANGO_SECRET_KEY`, disable debug mode, configure `DJANGO_ALLOWED_HOSTS`, use a production-ready WSGI or ASGI server, enable HTTPS, and review the upload and security settings. Do not deploy using `runserver`.
