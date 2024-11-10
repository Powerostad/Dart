
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

class CustomUser(AbstractUser):
    email = models.EmailField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
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
    address = models.CharField(max_length=255, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_picture_url = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    total_return = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    
    class Meta:
        indexes = [
            models.Index(fields=['user'], name='idx_profiles_userid'),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.user.username}"
    

class Stock(models.Model):
    stock_symbol = models.CharField(max_length=10, unique=True)
    company_name = models.CharField(max_length=255)
    market_cap = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    current_price = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['stock_symbol'], name='idx_stocks_symbol'),
        ]

    def __str__(self):
        return f"{self.stock_symbol} - {self.company_name}"
    
class Trade(models.Model):
    TRADE_TYPES = [
        ('Buy', 'Buy'),
        ('Sell', 'Sell'),
    ]

    profile = models.ForeignKey('Profile', on_delete=models.CASCADE)
    stock = models.ForeignKey('Stock', on_delete=models.CASCADE)
    trade_type = models.CharField(max_length=4, choices=TRADE_TYPES)
    quantity = models.IntegerField()
    trade_price = models.DecimalField(max_digits=15, decimal_places=2)
    trade_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['profile'], name='idx_trades_profileid'),
            models.Index(fields=['stock'], name='idx_trades_stockid'),
        ]

    def __str__(self):
        return f"{self.trade_type} - {self.stock.stock_symbol} - {self.quantity} shares"
    
class Watchlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stock = models.ForeignKey('Stock', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'stock')  # Ensure uniqueness of the User-Stock pair
        indexes = [
            models.Index(fields=['user'], name='idx_watchlist_userid'),
            models.Index(fields=['stock'], name='idx_watchlist_stockid'),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.stock.stock_symbol}"
    
    
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
    

class Alert(models.Model):
    ALERT_TYPES = [
        ('Price', 'Price'),
        ('Volume', 'Volume'),
        ('News', 'News'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stock = models.ForeignKey('Stock', on_delete=models.CASCADE)
    alert_type = models.CharField(max_length=6, choices=ALERT_TYPES)
    threshold = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user'], name='idx_alerts_userid'),
            models.Index(fields=['stock'], name='idx_alerts_stockid'),
        ]

    def __str__(self):
        return f"Alert: {self.alert_type} for {self.user.username} - {self.stock.stock_symbol}"
    

        