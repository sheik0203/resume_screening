from django import forms
from django.conf import settings


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        if not data:
            if self.required:
                raise forms.ValidationError("Upload at least one PDF resume.")
            return []

        files = data if isinstance(data, (list, tuple)) else [data]
        if len(files) > settings.MAX_RESUME_COUNT:
            raise forms.ValidationError(
                f"Upload no more than {settings.MAX_RESUME_COUNT} resumes at a time."
            )

        cleaned_files = []
        for uploaded_file in files:
            cleaned_file = super().clean(uploaded_file, initial)
            if not cleaned_file.name.lower().endswith(".pdf"):
                raise forms.ValidationError(
                    f"{cleaned_file.name}: only PDF files are accepted."
                )
            if cleaned_file.size > settings.MAX_RESUME_SIZE:
                limit_mb = settings.MAX_RESUME_SIZE // (1024 * 1024)
                raise forms.ValidationError(
                    f"{cleaned_file.name}: file exceeds the {limit_mb} MB limit."
                )
            cleaned_files.append(cleaned_file)
        return cleaned_files


class ResumeScreeningForm(forms.Form):
    job_description = forms.CharField(
        max_length=10_000,
        strip=True,
        widget=forms.Textarea(
            attrs={
                "rows": 8,
                "placeholder": "Paste the job description, including responsibilities and required skills...",
                "class": "form-control",
            }
        ),
        error_messages={"required": "Enter a job description before analyzing resumes."},
    )
    resumes = MultipleFileField(
        widget=MultipleFileInput(
            attrs={"accept": ".pdf,application/pdf", "class": "form-control"}
        ),
        error_messages={"required": "Upload at least one PDF resume."},
    )
