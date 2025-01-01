from rest_framework import serializers
from .models import Blog

class BlogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blog
        fields = ['id', 'title', 'content', 'author', 'status', 'created_at', 'updated_at', 'likes_count', 'image']
        read_only_fields = ['author', 'status', 'created_at', 'updated_at', 'likes_count']


class BlogDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blog
        fields = ['id', 'title', 'content', 'author', 'created_at', 'updated_at', 'image', 'likes_count']  # Include the image field


class BlogStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blog
        fields = ['status']