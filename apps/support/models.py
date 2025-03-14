from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class SupportThread(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="support_threads"
    )
    title = models.CharField(max_length=255)  # Subject of the thread
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class SupportMessage(models.Model):
    thread = models.ForeignKey(
        SupportThread, 
        on_delete=models.CASCADE, 
        related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="sent_support_messages"
    )
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_response = models.BooleanField(default=False)  # True if it's a response from support staff

    def __str__(self):
        return f"Message in {self.thread.title} by {self.sender}"