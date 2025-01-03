from rest_framework import serializers
from apps.blog.models import Blog

class BlogSerializer(serializers.ModelSerializer):
    content_preview = serializers.SerializerMethodField()

    class Meta:
        model = Blog
        fields = ['id', 'title', 'content_preview', 'author', 'likes_count', 'image']
        read_only_fields = ['author', 'likes_count']

    def get_content_preview(self, obj):
        # Return the first 200 characters of the content
        return obj.content[:200] + "..." if len(obj.content) > 200 else obj.content


class BlogDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blog
        fields = [ 'title', 'content', 'author',  'updated_at', 'image', 'likes_count']  # Include the image field


class BlogStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blog
        fields = ['status']