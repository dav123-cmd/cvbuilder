from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages

from .models import Resume, WorkExperience, CoverLetter
from .forms import (
    ResumeForm,
    WorkExperienceFormSet,
    EducationFormSet,
    SkillFormSet,
    CoverLetterRequestForm,
)
from . import ai_grok_service

# Free tier limits — keep these in one place so you can tune them without hunting through views
FREE_TIER_MAX_REGENERATIONS = 2
FREE_TIER_TEMPLATES = ["corporate"]

def home(request):
    return render(request,"resumebuilder/resume_list.html")
# ---------------------------------------------------------------------------
# Resume list / create / edit
# ---------------------------------------------------------------------------

@login_required
def resume_list(request):
    resumes = request.user.resumes.all()
    return render(request, "resumebuilder/resume_list.html", {"resumes": resumes})


@login_required
def resume_create(request):
    if request.method == "POST":
        form = ResumeForm(request.POST)
        if form.is_valid():
            resume = form.save(commit=False)
            resume.user = request.user
            resume.save()
            messages.success(request, "Resume started — now add your work experience.")
            return redirect("resume_edit", resume_id=resume.id)
    else:
        form = ResumeForm()
    return render(request, "resumebuilder/resume_form.html", {"form": form, "is_new": True})


@login_required
def resume_edit(request, resume_id):
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)

    if request.method == "POST":
        form = ResumeForm(request.POST, instance=resume)
        work_formset = WorkExperienceFormSet(request.POST, instance=resume, prefix="work")
        edu_formset = EducationFormSet(request.POST, instance=resume, prefix="edu")
        skill_formset = SkillFormSet(request.POST, instance=resume, prefix="skill")

        if all([form.is_valid(), work_formset.is_valid(), edu_formset.is_valid(), skill_formset.is_valid()]):
            form.save()
            work_formset.save()
            edu_formset.save()
            skill_formset.save()
            messages.success(request, "Resume saved.")
            return redirect("resume_edit", resume_id=resume.id)
    else:
        form = ResumeForm(instance=resume)
        work_formset = WorkExperienceFormSet(instance=resume, prefix="work")
        edu_formset = EducationFormSet(instance=resume, prefix="edu")
        skill_formset = SkillFormSet(instance=resume, prefix="skill")

    return render(request, "resumebuilder/resume_form.html", {
        "form": form,
        "work_formset": work_formset,
        "edu_formset": edu_formset,
        "skill_formset": skill_formset,
        "resume": resume,
        "is_new": False,
    })


# ---------------------------------------------------------------------------
# AI actions — called via fetch() from the edit page, return JSON
# ---------------------------------------------------------------------------

@login_required
@require_POST
def ai_rewrite_bullets(request, experience_id):
    experience = get_object_or_404(
        WorkExperience, id=experience_id, resume__user=request.user
    )
    resume = experience.resume

    if not resume.is_paid:
        used = request.session.get("regen_count", 0)
        if used >= FREE_TIER_MAX_REGENERATIONS:
            return JsonResponse(
                {"error": "Free regeneration limit reached. Upgrade to keep refining."},
                status=402,
            )
        request.session["regen_count"] = used + 1

    bullets = ai_grok_service.rewrite_bullet_points(
        job_title=experience.job_title,
        company=experience.company,
        raw_description=experience.raw_description,
        target_job_title=resume.target_job_title,
        target_job_description=resume.target_job_description,
    )
    experience.ai_bullet_points = "\n".join(bullets)
    experience.save(update_fields=["ai_bullet_points"])

    return JsonResponse({"bullets": bullets})


@login_required
@require_POST
def ai_generate_summary(request, resume_id):
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)

    work_data = [
        {"job_title": exp.job_title, "company": exp.company, "raw_description": exp.raw_description}
        for exp in resume.work_experiences.all()
    ]
    if not work_data:
        return JsonResponse({"error": "Add at least one work experience first."}, status=400)

    summary = ai_grok_service.generate_professional_summary(
        full_name=resume.full_name,
        work_experiences=work_data,
        target_job_title=resume.target_job_title,
        target_job_description=resume.target_job_description,
    )
    resume.professional_summary = summary
    resume.save(update_fields=["professional_summary"])

    return JsonResponse({"summary": summary})


@login_required
def cover_letter_create(request, resume_id):
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)

    if request.method == "POST":
        form = CoverLetterRequestForm(request.POST)
        if form.is_valid():
            work_data = [
                {"job_title": exp.job_title, "company": exp.company, "raw_description": exp.raw_description}
                for exp in resume.work_experiences.all()
            ]
            letter_text = ai_grok_service.generate_cover_letter(
                full_name=resume.full_name,
                work_experiences=work_data,
                job_title=form.cleaned_data["job_title"],
                company_name=form.cleaned_data["company_name"],
                job_description=form.cleaned_data["job_description"],
                tone=form.cleaned_data["tone"],
            )
            letter = CoverLetter.objects.create(
                resume=resume,
                job_title=form.cleaned_data["job_title"],
                company_name=form.cleaned_data["company_name"],
                generated_text=letter_text,
            )
            return redirect("cover_letter_view", resume_id=resume.id, letter_id=letter.id)
    else:
        form = CoverLetterRequestForm()

    return render(request, "resumebuilder/cover_letter_form.html", {"form": form, "resume": resume})


@login_required
def cover_letter_view(request, resume_id, letter_id):
    letter = get_object_or_404(CoverLetter, id=letter_id, resume_id=resume_id, resume__user=request.user)
    return render(request, "resumebuilder/cover_letter_detail.html", {"letter": letter})


# ---------------------------------------------------------------------------
# Preview / export — gated by tier
# ---------------------------------------------------------------------------

@login_required
def resume_preview(request, resume_id):
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)

    if not resume.is_paid and resume.template not in FREE_TIER_TEMPLATES:
        messages.warning(request, "That template is a paid feature. Upgrade to unlock it.")
        return redirect("resume_upgrade", resume_id=resume.id)

    return render(request, f"resumebuilder/templates_pdf/{resume.template}.html", {
        "resume": resume,
        "watermark": not resume.is_paid,
    })


@login_required
def resume_upgrade(request, resume_id):
    """Renders the paywall page. Actual STK push logic lives in payments.py (next piece)."""
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)
    return render(request, "resumebuilder/upgrade.html", {"resume": resume})



from .ai_grok_service import rewrite_bullet_points

def rewrite_experience_view(request, experience_id):
     exp = get_object_or_404(WorkExperience, id=experience_id, resume__user=request.user)
     bullets = rewrite_bullet_points(
       job_title=exp.job_title,
     company=exp.company,
        raw_description=exp.raw_description,
      target_job_title=exp.resume.target_job_title,
       target_job_description=exp.resume.target_job_description,
    )
     exp.ai_bullet_points = "\n".join(bullets)
     exp.save()
     return JsonResponse({"bullets": bullets})
