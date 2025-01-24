from django.db import models


class Signal(models.Model):
    symbol = models.CharField(max_length=20)
    timeframe = models.CharField(max_length=3)
    signal_type = models.CharField(max_length=10)
    confidence = models.DecimalField(max_digits=5, decimal_places=2)
    algorithms_triggered = models.JSONField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.symbol} ({self.timeframe}) - {self.signal_type} ({self.confidence}%)"

