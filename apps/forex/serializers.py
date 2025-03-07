from rest_framework import serializers
from apps.forex.models import Signal

class SignalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Signal
        fields = ["id", "symbol", "timeframe", "signal_type", "confidence"]


class SignalDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Signal
        fields = '__all__'

