from django.shortcuts import render,redirect,get_object_or_404
from .forms import RegisterForm,LoginForm,PasswordResetRequestForm, PasswordResetConfirmForm
from django.contrib import messages 
from django.contrib.auth import logout
from django.contrib.auth import login as auth_login
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from .models import User,PasswordResetToken
from .utils import send_password_reset_email
from django.utils import timezone


def home(request):
    return render(request,"resumebuilder/resume_list.html")

def register(request):
    if request.user.is_authenticated:
        return redirect("resume_list")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request,'Account Created Sucessfully')
        return redirect ('users:login')
    return render(request,"users/register.html",{'form':form})
    
def login(request):
    next_url = request.POST.get("next") or request.GET.get("next")
    if not url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        next_url = reverse("resume_list")

    if request.user.is_authenticated:
        return redirect(next_url)

    form = LoginForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        auth_login(request, user)
        if not form.cleaned_data.get("remember"):
            request.session.set_expiry(0)
        messages.success(request, f"Welcome back, {user.get_short_name()}.")
        return redirect(next_url)

    return render(request, "users/login.html", {"form": form, "next": next_url})
    
    
def logout_view(request):
    logout(request)
    messages.info(request,'You have been Logout Out')
    return redirect ("resume_list")

def password_reset_request(request):
    form=PasswordResetRequestForm(request.POST or None ,request.FILES or None)
    if request.method == "POST" and form.is_valid():
        email=form.cleaned_data['email']
        user=User.objects.get(email__iexact=email)
        send_password_reset_email(user,email)
        messages.success(request,'Password Reset Link sent to Your Email')
        return redirect("users:login")
    return render(request,"users/password_reset.html",{"form":form})

def password_reset_confirm(request,token):
    token_obj=get_object_or_404(PasswordResetToken,token=token)
    if timezone.now() > token_obj.expires_at:
        token_obj.delete()
        messages.error(request,"This Password rest link has expired request a new one")
        return redirect("user:login")
    form=PasswordResetConfirmForm(request.POST or None )
    if request.method == "POST" and form.is_valid():
        user=token_obj.user
        user.set_password(form.cleaned_data.get('new_password1'))
        user.save()
        token_obj.delete()
        messages.success(request,'Password reset successfull! You can now login in.')
        return redirect("user:login")
    return render(request,"users/password_reset_confirm.html",{"form":form})
    
