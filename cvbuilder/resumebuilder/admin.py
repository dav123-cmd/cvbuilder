from django.contrib import admin
from .models import Resume, WorkExperience, Education, Skill, CoverLetter, Payment


class WorkExperienceInline(admin.TabularInline):
    model = WorkExperience
    extra = 0


class EducationInline(admin.TabularInline):
    model = Education
    extra = 0


class SkillInline(admin.TabularInline):
    model = Skill
    extra = 0


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ("full_name", "user", "template", "tier", "updated_at")
    list_filter = ("template", "tier")
    search_fields = ("full_name", "email", "user__username")
    inlines = [WorkExperienceInline, EducationInline, SkillInline]


@admin.register(CoverLetter)
class CoverLetterAdmin(admin.ModelAdmin):
    list_display = ("resume", "job_title", "company_name", "created_at")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("resume", "phone_number", "amount", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("phone_number", "checkout_request_id", "mpesa_receipt_number")
