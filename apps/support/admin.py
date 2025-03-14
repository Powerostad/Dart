from django.contrib import admin
from apps.support.models import SupportThread, SupportMessage

@admin.register(SupportThread)
class SupportThreadAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'title', 'created_at', 'updated_at']
    search_fields = ['title', 'user__username']

@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'thread', 'sender', 'is_response', 'sent_at']
    list_filter = ['is_response', 'sent_at']
    search_fields = ['thread__title', 'sender__username', 'content']
