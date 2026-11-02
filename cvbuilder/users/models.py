from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.utils import timezone
import uuid

class UserManager(BaseUserManager):
    def create_user(self, email, date_of_birth, password=None):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not email:
            raise ValueError("Users must have an email address")

        user = self.model(
            email=self.normalize_email(email),
            date_of_birth=date_of_birth,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, date_of_birth, password=None):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            email,
            password=password,
            date_of_birth=date_of_birth,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    first_name=models.CharField(max_length=21)
    last_name=models.CharField(max_length=21)
    email = models.EmailField(
        verbose_name="email address",
        max_length=255,
        unique=True,
    )
    date_of_birth =models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["date_of_birth"]

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True
    
    def get_user_fullname(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_short_name(self):
        return f"{self.first_name}"
    
    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin
    
class PasswordResetToken(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='reset_tokens')
    token=models.UUIDField(default=uuid.uuid4,unique=True)
    created_at=models.DateField(auto_now_add=True)
    expires_at=models.DateField(default=False)
    used=models.BooleanField(default=False)
    
    def is_valid(self):
        return not self.used and timezone.now() < self.expires_at
    
class EmailVerification(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='verification_tokens')
    token=models.UUIDField(default=uuid.uuid4,unique=True)
    created_at=models.DateField(auto_now_add=True)
    expires_at=models.DateField(default=False)
    used=models.BooleanField(default=False)
    
    def is_valid(self):
        return timezone.now() < self.expires_at
    