from venv import logger
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
import uuid
import qrcode
from io import BytesIO
from django.core.files import File
from django.conf import settings

class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **kwargs):
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **kwargs)
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
        return self._create_user(email, password, **kwargs)

class CustomUser(AbstractUser):

    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField('email address', unique=True)
    user_type = models.CharField(max_length=10, choices=(('client', 'Client'), ('waiter', 'Waiter')))
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_payment_method_id = models.CharField(max_length=255, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

class WaiterProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    workplace = models.CharField(max_length=255)
    goal = models.TextField(blank=True, null=True)
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True)
    photo = models.ImageField(upload_to='photos/', blank=True, null=True) 

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        logger.debug("Saving WaiterProfile for user: %s", self.user.email)
        if not self.qr_code:
            qr_content = f"{settings.SITE_URL}/make-tip/{self.user.id}/"
            qr_image = qrcode.make(qr_content)
            qr_offset = BytesIO()
            qr_image.save(qr_offset, format='PNG')
            qr_file_name = f"{self.user.id}_qrcode.png"
            self.qr_code.save(qr_file_name, File(qr_offset), save=False)
        super().save(*args, **kwargs)
        
class ClientProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    nickname = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nickname

class Tip(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    waiter = models.ForeignKey(WaiterProfile, on_delete=models.CASCADE)
    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    review = models.TextField(blank=True, null=True)
    rating = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"Tip from {self.client.nickname} to {self.waiter.user.email} - {self.amount}"


class PaymentMethod(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    card_number = models.CharField(max_length=16)
    card_type = models.CharField(max_length=50)
    expiration_date = models.CharField(max_length=5)
    cvc = models.CharField(max_length=3)

    def __str__(self):
        return f"{self.card_type} ending in {self.card_number[-4:]}"