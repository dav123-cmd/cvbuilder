from django import forms 
from django.contrib.auth import authenticate,get_user_model
from django.contrib.auth.password_validation import validate_password
User=get_user_model()



class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def clean_email(self):
        email = self.cleaned_data.get("email", "").lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists")
        return email 

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError({'password2': 'Passwords do not match'})
        if p1:
            validate_password(p1, user=None)
        return cleaned_data 

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user







"""
class RegisterForm(forms.ModelForm):
    password1=forms.CharField(widget=forms.PasswordInput,label="Password")
    password2=forms.CharField(widget=forms.PasswordInput,label="Confirm Password")
    class Meta:
        model=User
        fields={'first_name','last_name','email'}
        def clean_email(self):
            email=self.clean_data_get("email",'').lower()
            if User.objects.filter(email=email).exits():
                raise forms.ValidationError("An account with this email Already exits")
            return email 
        def clean_password(self):
            cleaned_data=super().clean()
            p1=cleaned_data.get('password1')
            p2=cleaned_data.get('password2')
            
            if p1 and p2 and p1 != p2:
                raise forms.ValidationError({'password2':'Password do not match'})
            if p1:
                validate_password(p1,user=None)
            return cleaned_data 
        def save(self,commit=True):
            user=super().save(commit=False)
            user.set_password(self.cleaned_data["password1"])
            if commit:
                user.save()
            return user
 """     
        
from django import forms
from django.contrib.auth import authenticate

class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    remember = forms.BooleanField(required=False, initial=False, label="Remember Me")

    def __init__(self, *args, **kwargs):
        # Capture the request object passed from the view if needed
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email', "").lower()
        password = cleaned_data.get('password')
        
        if email and password:
            # Use 'username=email' so Django's auth backend picks it up correctly
            user = authenticate(self.request, username=email, password=password)
            
            if user is None:
                raise forms.ValidationError("Invalid email or Password")
            if not user.is_active:
                raise forms.ValidationError('This account has been deactivated')
                
            self.user = user
        return cleaned_data

    def get_user(self):
        return getattr(self, 'user', None)

 
"""      
class LoginForm(forms.Form):
    email=forms.EmailField()
    password=forms.CharField(widget=forms.PasswordInput)
    remember=forms.BooleanField(required=False,initial=False,label="Remember Me")
    def clean(self,request):
        cleaned_data=super().clean()
        email=cleaned_data.get('email',"").lower()
        password=cleaned_data.get('password')
        
        if email and password:
            user=authenticate(request,username=email,password=password)
            if user is None:
                raise forms.ValidationError("Invalid email or Password")
            if not user.is_active:
                raise forms.ValidationError('This account has been deactivated')
            self.user=user
        return cleaned_data
    def get_user(self):
     return getattr(self,'user',None)
"""
                
            



class PasswordResetRequestForm(forms.ModelForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'})
    )
    
    def clean_email(self):
       
        email = self.cleaned_data.get('email', '').lower() or self.data.get('email', '')
        
        
        if not User.objects.filter(email=email, is_active=True).exists():
            raise forms.ValidationError("An account with this email does not exist.")
        return email 

    class Meta:
        model = User
        fields = ['email']  


class PasswordResetConfirmForm(forms.Form):
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password1')  
        p2 = cleaned_data.get('new_password2')  
                
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError({'new_password2': 'Passwords do not match.'})
        
        if p1:
            validate_password(p1)
            
        return cleaned_data