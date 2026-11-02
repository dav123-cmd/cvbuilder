from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
app_name='users'

urlpatterns = [
  path('',views.home,name="homwe"),
   path('login/', views.login, name='login'),
   path('register/',views.register,name='register'),
   path('logout/',views.logout_view,name='logout'), 
  path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/confirm/<str:token>/', views.password_reset_confirm, name='password_reset_confirm'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)