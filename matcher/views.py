import logging

from django.contrib import messages
from django.shortcuts import render

from .forms import ResumeScreeningForm
from .services import ResumeExtractionError, extract_pdf_text, rank_resumes

logger = logging.getLogger(__name__)


def upload_resumes(request):
    if request.method == "POST":
        form = ResumeScreeningForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(
                request,
                "matcher/upload.html",
                {"form": form},
                status=400,
            )

        candidates = []
        processing_errors = []
        for uploaded_file in form.cleaned_data["resumes"]:
            try:
                candidates.append(
                    {
                        "filename": uploaded_file.name,
                        "text": extract_pdf_text(uploaded_file),
                    }
                )
            except ResumeExtractionError as exc:
                processing_errors.append(f"{uploaded_file.name}: {exc}")
            except Exception:
                logger.exception("Unexpected error while processing an uploaded resume")
                processing_errors.append(
                    f"{uploaded_file.name}: An unexpected error occurred while reading this PDF."
                )

        if not candidates:
            return render(
                request,
                "matcher/upload.html",
                {
                    "form": form,
                    "processing_errors": processing_errors,
                },
                status=400,
            )

        try:
            results = rank_resumes(
                form.cleaned_data["job_description"], candidates
            )
        except ValueError as exc:
            form.add_error("job_description", str(exc))
            return render(
                request,
                "matcher/upload.html",
                {
                    "form": form,
                    "processing_errors": processing_errors,
                },
                status=400,
            )

        if processing_errors:
            messages.warning(
                request,
                f"{len(processing_errors)} resume(s) could not be analyzed.",
            )
        return render(
            request,
            "matcher/results.html",
            {
                "results": results,
                "processing_errors": processing_errors,
                "job_description": form.cleaned_data["job_description"],
            },
        )

    return render(request, "matcher/upload.html", {"form": ResumeScreeningForm()})
