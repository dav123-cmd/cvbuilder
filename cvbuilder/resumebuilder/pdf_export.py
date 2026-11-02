

import io
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

from weasyprint import HTML
from .models import Resume


def render_resume_pdf_bytes(resume: Resume) -> bytes:
    """
    Renders resume.template to PDF bytes. Reuses the exact same template
    used for the on-screen preview, so anything you tweak in
    templates_pdf/*.html shows up in both places automatically.
    """
    html_string = render_to_string(
        f"resumebuilder/templates_pdf/{resume.template}.html",
        {"resume": resume, "watermark": not resume.is_paid},
    )
    pdf_bytes = HTML(string=html_string).write_pdf()
    return pdf_bytes


@login_required
def resume_download_pdf(request, resume_id):
    """
    Streams the PDF as a download. Filename reflects the candidate's name
    so it doesn't land in their downloads folder as 'corporate.pdf'.
    """
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)

    pdf_bytes = render_resume_pdf_bytes(resume)

    safe_name = "".join(c for c in resume.full_name if c.isalnum() or c in " -_").strip() or "resume"
    filename = f"{safe_name.replace(' ', '_')}_CV.pdf"

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@login_required
def cover_letter_download_pdf(request, resume_id, letter_id):
    """
    Cover letters get a simpler, template-independent PDF — no need to
    match the resume's visual style, just clean and printable.
    """
    from .models import CoverLetter

    letter = get_object_or_404(CoverLetter, id=letter_id, resume_id=resume_id, resume__user=request.user)

    html_string = render_to_string("resumebuilder/templates_pdf/cover_letter.html", {"letter": letter})
    pdf_bytes = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="cover_letter.pdf"'
    return response
