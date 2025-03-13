
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.db import models
from django.conf import settings
from django.utils.crypto import get_random_string
from phonenumber_field.modelfields import PhoneNumberField

from utils.utils import validate_image_file


# from apps.dashboard.models import Stock

class CustomUser(AbstractUser):
    email = models.EmailField(max_length=255, unique=True)
    phone_number = PhoneNumberField(unique=True, region="IR")
    plan = models.ForeignKey(to="SubscriptionPlan", on_delete=models.PROTECT, related_name="users", default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    referral_code = models.CharField(max_length=10, unique=True, blank=True)
    referral_points = models.PositiveIntegerField(default=0)
    referred_by = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='referrals'
    )

    def save(self, *args, **kwargs):
        if not self.referral_code:
            while True:
                code = get_random_string(10, allowed_chars='ABCDEFGHJKLMNPQRSTUVWXYZ23456789')
                if not CustomUser.objects.filter(referral_code=code).exists():
                    self.referral_code = code
                    break
        super().save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=['email'], name='idx_users_email'),
        ]

    def __str__(self):
        return self.username
    

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/%Y/%m/', blank=True, null=True,
                                        validators=[
                                            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png']),
                                            validate_image_file
                                        ]
                                        )
    bio = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    
    class Meta:
        indexes = [
            models.Index(fields=['user'], name='idx_profiles_userid'),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.user.username}"

    @property
    def profile_picture_url(self):
        """Return the full URL to the profile picture or a default if none exists"""
        if self.profile_picture:
            return self.profile_picture.url
        return f"{settings.MINIO_HOST}/{settings.MINIO_IMAGE_PROFILE_BUCKET}/default.jpeg"


# class Trade(models.Model):
#     TRADE_TYPES = [
#         ('Buy', 'Buy'),
#         ('Sell', 'Sell'),
#     ]
#
#     profile = models.ForeignKey('Profile', on_delete=models.CASCADE)
#     stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
#     trade_type = models.CharField(max_length=4, choices=TRADE_TYPES)
#     quantity = models.IntegerField()
#     trade_price = models.DecimalField(max_digits=15, decimal_places=2)
#     trade_date = models.DateTimeField(auto_now_add=True)
#
#     class Meta:
#         indexes = [
#             models.Index(fields=['profile'], name='idx_trades_profileid'),
#             models.Index(fields=['stock'], name='idx_trades_stockid'),
#         ]
#
#     def __str__(self):
#         return f"{self.trade_type} - {self.stock.stock_symbol} - {self.quantity} shares"
    

    
class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('Deposit', 'Deposit'),
        ('Withdrawal', 'Withdrawal'),
    ]

    profile = models.ForeignKey('Profile', on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    transaction_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['profile'], name='idx_transactions_profileid'),
        ]

    def __str__(self):
        return f"{self.transaction_type} - {self.profile.user.username} - {self.amount}"     
    

# class Alert(models.Model):
#     ALERT_TYPES = [
#         ('Price', 'Price'),
#         ('Volume', 'Volume'),
#         ('News', 'News'),
#     ]
#
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
#     stock = models.ForeignKey('Stock', on_delete=models.CASCADE)
#     alert_type = models.CharField(max_length=6, choices=ALERT_TYPES)
#     threshold = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#
#     class Meta:
#         indexes = [
#             models.Index(fields=['user'], name='idx_alerts_userid'),
#             models.Index(fields=['stock'], name='idx_alerts_stockid'),
#         ]
#
#     def __str__(self):
#         return f"Alert: {self.alert_type} for {self.user.username} - {self.stock.stock_symbol}"

class SubscriptionPlan(models.Model):
    BILLING_CHOICES = [
        ("monthly", "Monthly"),
        ("yearly", "Yearly"),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=15, decimal_places=3)
    billing_interval = models.CharField(max_length=255, choices=BILLING_CHOICES, default="monthly")
    features = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.price}/{self.billing_interval}"

    class Meta:
        verbose_name = "Subscription Plan"
        verbose_name_plural = "Subscription Plans"
        db_table = "subscription_plans"
        unique_together = ("name", "price", "billing_interval")

