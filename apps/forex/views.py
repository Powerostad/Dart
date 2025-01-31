from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.forex.models import Signal
from apps.forex.serializers import SignalSerializer

class SignalView(APIView):
    serializer_class = SignalSerializer

    def get(self, request):
        timeframe = request.query_params.get('timeframe', None)
        symbol = request.query_params.get('symbol', None)

        filters = {}
        if timeframe:
            filters['timeframe'] = timeframe
        if symbol:
            filters['symbol'] = symbol

        signals = Signal.objects.filter(**filters)
        serializer = SignalSerializer(signals, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)