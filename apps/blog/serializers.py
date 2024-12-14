from rest_framework import serializers
from .models import Blog

class BlogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blog
        fields = ['id', 'title', 'content', 'author', 'status', 'created_at', 'updated_at', 'likes_count']
        read_only_fields = ['author', 'status', 'created_at', 'updated_at', 'likes_count']
