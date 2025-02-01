from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.forex.models import Signal
from apps.forex.serializers import SignalSerializer
from utils.utils import StandardResultsSetPagination


class SignalView(APIView):
    serializer_class = SignalSerializer
    pagination_class = StandardResultsSetPagination

    def get(self, request):
        # Initialize pagination
        paginator = self.pagination_class()

        # Apply filters
        timeframe = request.query_params.get('timeframe', None)
        symbol = request.query_params.get('symbol', None)

        filters = {}
        if timeframe:
            filters['timeframe'] = timeframe
        if symbol:
            filters['symbol'] = symbol

        # Get queryset with filters
        signals = Signal.objects.filter(**filters)

        # Paginate results
        paginated_signals = paginator.paginate_queryset(signals, request)

        # Serialize data
        serializer = SignalSerializer(paginated_signals, many=True)

        # Return paginated response
        return paginator.get_paginated_response(serializer.data)