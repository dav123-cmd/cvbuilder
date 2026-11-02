from django import forms
from django.forms import inlineformset_factory
from .models import Resume, WorkExperience, Education, Skill, CoverLetter


class ResumeForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = [
            "full_name",
            "email",
            "phone",
            "location",
            "professional_summary",
            "template",
            "target_job_title",
            "target_job_description",
        ]
        widgets = {
            "professional_summary": forms.Textarea(
                attrs={"rows": 4, "placeholder": "Leave blank and we'll draft one for you with AI"}
            ),
            "target_job_description": forms.Textarea(
                attrs={"rows": 6, "placeholder": "Paste the job description you're applying to"}
            ),
            "template": forms.Select(attrs={"class": "form-select"}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "")
        digits = "".join(ch for ch in phone if ch.isdigit())
        if digits.startswith("0"):
            digits = "254" + digits[1:]
        return digits


class WorkExperienceForm(forms.ModelForm):
    class Meta:
        model = WorkExperience
        fields = [
            "job_title",
            "company",
            "location",
            "start_date",
            "end_date",
            "is_current",
            "raw_description",
        ]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "raw_description": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Describe what you did in plain language — AI will turn this into strong bullet points",
                }
            ),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("is_current"):
            cleaned["end_date"] = None
        elif not cleaned.get("end_date"):
            raise forms.ValidationError("Provide an end date, or mark this as your current role.")
        return cleaned


class EducationForm(forms.ModelForm):
    class Meta:
        model = Education
        fields = ["institution", "qualification", "start_date", "end_date", "notes"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }


class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ["name"]
        widgets = {"name": forms.TextInput(attrs={"placeholder": "e.g. Django, Team Leadership"})}


class CoverLetterRequestForm(forms.Form):
   

    job_title = forms.CharField(max_length=150, required=False)
    company_name = forms.CharField(max_length=150, required=False)
    job_description = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 6}),
        help_text="Paste the job ad — the more detail, the better the tailoring.",
    )
    tone = forms.ChoiceField(
        choices=[("formal", "Formal"), ("friendly", "Friendly but professional"), ("confident", "Confident")],
        initial="formal",
    )


# Formsets — let a user add multiple work experiences / education entries / skills
# against a single Resume in one page
WorkExperienceFormSet = inlineformset_factory(
    Resume,
    WorkExperience,
    form=WorkExperienceForm,
    extra=1,
    can_delete=True,
)

EducationFormSet = inlineformset_factory(
    Resume,
    Education,
    form=EducationForm,
    extra=1,
    can_delete=True,
)

SkillFormSet = inlineformset_factory(
    Resume,
    Skill,
    form=SkillForm,
    extra=3,
    can_delete=True,
)
