from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Stock(models.Model):
    stock_symbol = models.CharField(max_length=10, unique=True)
    current_price = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['stock_symbol'], name='idx_stocks_symbol'),
        ]

    def __str__(self):
        return f"{self.stock_symbol} - {self.current_price}"


class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlist')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='watchlist')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'stock')  # Ensure uniqueness of the User-Stock pair
        indexes = [
            models.Index(fields=['user'], name='idx_watchlist_userid'),
            models.Index(fields=['stock'], name='idx_watchlist_stockid'),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.stock.stock_symbol}"

