from io import BytesIO
import uuid
from django.conf import settings
from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
import qrcode
from stripe import File

class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **kwargs):
        if not email:
            raise ValueError('The given email must be set!')
        email = self.normalize_email(email=email)
        user = self.model(email=email, **kwargs)
        user.create_activation_code()
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_user(self, email, password=None, **kwargs):
        kwargs.setdefault('is_staff', False)
        kwargs.setdefault('is_superuser', False)
        return self._create_user(email, password, **kwargs)
    
    def create_superuser(self, email, password, **kwargs):
        kwargs.setdefault('is_staff', True)
        kwargs.setdefault('is_superuser', True)
        kwargs.setdefault('is_active', True)
        if kwargs.get('is_staff') is not True:
            raise ValueError('Superuser must have status is_staff=True')
        if kwargs.get('is_superuser') is not True:
            raise ValueError('Superuser must have status is_superuser=True')
        return self._create_user(email, password, **kwargs)

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('waiter', 'Waiter'),
        ('client', 'Client'),
    )
    username=None
    email = models.EmailField('email address', unique=True)
    password = models.CharField(max_length=100)
    activation_code = models.CharField(max_length=255, blank=True)
    user_type = models.CharField(max_length=6, choices=USER_TYPE_CHOICES)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    is_active = models.BooleanField(
        _('active'),
        default=False,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'))

    def __str__(self):
        return self.email
    
    def create_activation_code(self):
        code = str(uuid.uuid4())
        self.activation_code = code

class WaiterProfile(models.Model):
    user = models.OneToOneField('accounts.CustomUser', on_delete=models.CASCADE, primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    workplace = models.CharField(max_length=255)
    # wallet = models.CharField(max_length=255, blank=True, null=True)
    # payment_method = models.CharField(max_length=255, blank=True, null=True)
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def save(self, *args, **kwargs):
        qr_content = f"{settings.SITE_URL}/make-tip/{self.user.id}/"
        qr_image = qrcode.make(qr_content)
        qr_offset = BytesIO()
        qr_image.save(qr_offset, format='PNG')
        qr_file_name = f"{self.user.id}_qrcode.png"
        self.qr_code.save(qr_file_name, File(qr_offset), save=False)
        super().save(*args, **kwargs)

class ClientProfile(models.Model):
    user = models.OneToOneField('accounts.CustomUser', on_delete=models.CASCADE, primary_key=True)
    nickname = models.CharField(max_length=100, unique=True)
    # payment_method = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.nickname

