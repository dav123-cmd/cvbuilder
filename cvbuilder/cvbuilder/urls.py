
from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path("users/", include("users.urls")),
    path("resume/", include("resumebuilder.urls")),
    path("", RedirectView.as_view(pattern_name="resume_list", permanent=False), name="home"),
]
