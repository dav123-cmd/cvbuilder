import uuid
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class Resume(models.Model):
    """The main resume document a user is building."""

    TEMPLATE_CHOICES = [
        ("corporate", "Corporate"),
        ("ngo", "NGO"),
        ("gig", "Gig / Freelance"),
        ("minimal", "Minimal"),
    ]

    TIER_CHOICES = [
        ("free", "Free"),
        ("paid", "Paid"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL , on_delete=models.CASCADE, related_name="resumes")

    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=100, blank=True, help_text="e.g. Nairobi, Kenya")
    professional_summary = models.TextField(blank=True, help_text="AI-generated or user-edited summary")

    template = models.CharField(max_length=20, choices=TEMPLATE_CHOICES, default="corporate")
    tier = models.CharField(max_length=10, choices=TIER_CHOICES, default="free")

    # Job targeting — pasted job description used to tailor the resume/cover letter
    target_job_description = models.TextField(blank=True)
    target_job_title = models.CharField(max_length=150, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.full_name} - {self.template} ({self.tier})"

    @property
    def is_paid(self):
        return self.tier == "paid"


class WorkExperience(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="work_experiences")

    job_title = models.CharField(max_length=150)
    company = models.CharField(max_length=150)
    location = models.CharField(max_length=100, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)

    raw_description = models.TextField(help_text="What the user typed, in their own words")
    ai_bullet_points = models.TextField(
        blank=True, help_text="AI-rewritten bullet points, stored as newline-separated text"
    )

    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "-start_date"]

    def __str__(self):
        return f"{self.job_title} at {self.company}"

    def bullet_list(self):
        """Convenience accessor for template rendering."""
        source = self.ai_bullet_points or self.raw_description
        return [line.strip("-• ").strip() for line in source.splitlines() if line.strip()]


class Education(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="education_entries")

    institution = models.CharField(max_length=150)
    qualification = models.CharField(max_length=150, help_text="e.g. BSc Computer Science")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True)

    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "-end_date"]
        verbose_name_plural = "Education entries"

    def __str__(self):
        return f"{self.qualification} - {self.institution}"


class Skill(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="skills")
    name = models.CharField(max_length=80)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name


class CoverLetter(models.Model):
    """AI-generated cover letter tied to a resume + specific job application."""

    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="cover_letters")
    job_title = models.CharField(max_length=150, blank=True)
    company_name = models.CharField(max_length=150, blank=True)
    generated_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Cover letter for {self.job_title or 'unspecified role'}"


class Payment(models.Model):
    

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
    ]

    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="payments")
    phone_number = models.CharField(max_length=15, help_text="Format: 2547XXXXXXXX")
    amount = models.DecimalField(max_digits=8, decimal_places=2)

    checkout_request_id = models.CharField(max_length=100, blank=True, db_index=True)
    merchant_request_id = models.CharField(max_length=100, blank=True)
    mpesa_receipt_number = models.CharField(max_length=50, blank=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    raw_callback = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"KES {self.amount} - {self.status}"
