from django.contrib import admin
from .models import Blog

@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_at', 'updated_at']
# Register your models here.
