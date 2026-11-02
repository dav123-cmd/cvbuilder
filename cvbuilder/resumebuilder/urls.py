from django.urls import path
from . import views
from . import payments
from . import pdf_export

urlpatterns = [
    path('',views.home,name='home'),
    
    path("<uuid:resume_id>/upgrade/initiate/", payments.upgrade_initiate, name="upgrade_initiate"),
    path("<uuid:resume_id>/upgrade/status/", payments.upgrade_status, name="upgrade_status"),
    path("mpesa/callback/", payments.mpesa_callback, name="mpesa_callback"),

    path("<uuid:resume_id>/download/", pdf_export.resume_download_pdf, name="resume_download_pdf"),
    path("<uuid:resume_id>/cover-letter/<int:letter_id>/download/",
         pdf_export.cover_letter_download_pdf, name="cover_letter_download_pdf"),

    path("", views.resume_list, name="resume_list"),
    path("new/", views.resume_create, name="resume_create"),
    path("<uuid:resume_id>/edit/", views.resume_edit, name="resume_edit"),
    path("<uuid:resume_id>/preview/", views.resume_preview, name="resume_preview"),
    path("<uuid:resume_id>/upgrade/", views.resume_upgrade, name="resume_upgrade"),

    # AI actions (called via fetch/AJAX from the edit page)
    path("experience/<int:experience_id>/rewrite/", views.ai_rewrite_bullets, name="ai_rewrite_bullets"),
    path("<uuid:resume_id>/generate-summary/", views.ai_generate_summary, name="ai_generate_summary"),

    # Cover letters
    path("<uuid:resume_id>/cover-letter/new/", views.cover_letter_create, name="cover_letter_create"),
    path("<uuid:resume_id>/cover-letter/<int:letter_id>/", views.cover_letter_view, name="cover_letter_view"),
    
   
]
