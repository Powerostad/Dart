import asyncio
import json
import logging
from typing import Dict, Any, Optional

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from utils.algorithms.algorithms import (
    AligatorAlgorithm,
    NadayaraWatsonFullStrategy15Min,
    MHarrisSystematic
)
from utils.signal_manager.signal_manager import SignalManager

User = get_user_model()
logger = logging.getLogger(__name__)


class SignalConsumer(AsyncWebsocketConsumer):
    SIGNAL_INTERVAL = 5  # seconds
    ERROR_WAIT_INTERVAL = 60  # seconds
    TRADE_PERCENTAGE = 0.02
    TPSL_RATIO = 1.5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.symbol: str = ''
        self.manager: Optional[SignalManager] = None
        self._signal_task: Optional[asyncio.Task] = None

    async def connect(self):
        """Handle new WebSocket connection."""
        try:
            # Validate user authentication
            await self.validate_user()

            # Extract and validate symbol
            self.symbol = self.scope['url_route']['kwargs']['symbol'].upper()
            await self.validate_symbol()

            # Initialize signal manager with algorithms
            self.manager = SignalManager(self.symbol)
            self._setup_algorithms()

            # Accept connection and start signal generation
            await self.accept()
            self._signal_task = asyncio.create_task(self._generate_signals())

        except Exception as e:
            logger.error(f"Connection error: {e}")
            await self.close(code=4001)

    async def validate_user(self):
        """Validate user authentication."""
        if not self.scope['user'].is_authenticated:
            raise PermissionError("Unauthorized access")

    async def validate_symbol(self):
        """Validate symbol format and permissions."""
        # Add custom validation logic here
        if not self.symbol or len(self.symbol) > 10:
            raise ValueError("Invalid symbol")

    def _setup_algorithms(self):
        """Configure signal generation algorithms."""
        algorithms = [
            AligatorAlgorithm(),
            MHarrisSystematic(),
            NadayaraWatsonFullStrategy15Min()
        ]
        for algo in algorithms:
            self.manager.add_algorithm(algo)

    async def _generate_signals(self):
        """Continuously generate and send trading signals."""
        try:
            while True:
                signal_data = await self._get_signal()
                await self._send_signal(signal_data)
                await asyncio.sleep(self.SIGNAL_INTERVAL)
        except asyncio.CancelledError:
            logger.info("Signal generation stopped")
        except Exception as e:
            logger.error(f"Signal generation error: {e}")
            # Implement adaptive backoff or reconnection strategy
            await asyncio.sleep(self.ERROR_WAIT_INTERVAL)

    async def _get_signal(self) -> Dict[str, Any]:
        """Fetch trading signal with thread-safe execution."""
        loop = asyncio.get_event_loop()
        signal = await loop.run_in_executor(None, self.manager.get_signal)

        if signal == 'hold':
            return {
                'signal': 'hold',
                'entry_price': None
            }

        return self._calculate_trade_details(signal)

    def _calculate_trade_details(self, signal: str) -> Dict[str, Any]:
        """Calculate trade details based on signal."""
        entry_price = self.manager.data_handler.get_data()["Close"].iloc[-1]
        message = {
            'signal': signal,
            'entry_price': entry_price
        }

        perc = self.TRADE_PERCENTAGE
        if signal == "buy":
            message.update({
                'sl': entry_price - entry_price * perc,
                'tp': entry_price + entry_price * perc * self.TPSL_RATIO
            })
        elif signal == "sell":
            message.update({
                'sl': entry_price + entry_price * perc,
                'tp': entry_price - entry_price * perc * self.TPSL_RATIO
            })

        return message

    async def _send_signal(self, signal_data: Dict[str, Any]):
        """Send signal data over WebSocket."""
        try:
            await self.send(text_data=json.dumps(signal_data))
        except Exception as e:
            logger.error(f"Signal sending error: {e}")

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if self._signal_task:
            self._signal_task.cancel()
        logger.info(f"Connection closed with code: {close_code}")