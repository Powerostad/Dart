from rest_framework import serializers
from apps.support.models import SupportThread, SupportMessage

class SupportThreadSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportThread
        fields = ['id', 'user', 'title', 'created_at', 'updated_at']

class SupportMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportMessage
        fields = ['id', 'thread', 'sender', 'content', 'sent_at', 'is_response']
