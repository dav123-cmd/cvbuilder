
from django.template.loader import render_to_string 
from django.core.mail import send_mail
from .models import PasswordResetToken 
from django.conf import settings 
from django.utils  import timezone 
from django.urls import reverse 
from datetime import timedelta

def send_password_reset_email(user,request):
    token=PasswordResetToken.objects.create(user=user,expires_at=timezone.now()+timedelta(hours=2))
    relative_url=reverse("users:password_reset_confirm",
                         kwargs={'token':str(token.token)})
    reset_url=request.build_absolute_uri(relative_url)
    send_mail(
        subject='Reset Your CVDraft',
        message=f"Click to Reset Your Password:{reset_url}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=render_to_string("users/email/password_reset_email.html",{
            "user":user,
            "reset_url":reset_url,
            
        }),
        fail_silently=False
    )