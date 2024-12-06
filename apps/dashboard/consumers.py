import asyncio
import json
import logging
from typing import Dict, Any, Optional, List

from django.contrib.auth import get_user_model
from channels.generic.websocket import AsyncWebsocketConsumer

from utils.algorithms.algorithms import (
    AligatorAlgorithm,
    NadayaraWatsonFullStrategy15Min,
    MHarrisSystematic
)
from utils.signal_manager.signal_manager import SignalManager
from utils.timeframes import mt5

User = get_user_model()
logger = logging.getLogger(__name__)


SCALPING_ASSETS = [
    # Stocks
    "AAPL.NAS", "AMZN.NAS", "MSFT.NAS", "GOOGL.NAS", "TSLA.NAS", "NVDA.NAS", "META.NAS", "NFLX.NAS", "BABA.NAS",
    "JPM.NAS", "GS.NAS", "BA.NAS", "INTC.NAS", "KO.NAS", "V.NAS", "PFE.NAS",
    # Currency Pairs
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD", "USDCAD", "EURGBP", "EURJPY", "GBPJPY"
]

class SignalConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for generating and streaming trading signals.

    Responsibilities:
    - Manage authenticated WebSocket connections
    - Generate real-time trading signals
    - Handle signal generation for multiple symbols
    - Implement adaptive error handling
    """

    # Configuration Parameters
    SIGNAL_INTERVAL = 5  # seconds
    ERROR_WAIT_INTERVAL = 60  # seconds
    TRADE_PERCENTAGE = 0.02
    TPSL_RATIO = 1.5

    def __init__(self, *args, **kwargs):
        """
        Initialize WebSocket consumer with flexible configuration.
        """
        super().__init__(*args, **kwargs)
        self.symbols: List[str] = SCALPING_ASSETS
        self.manager: Optional[SignalManager] = None
        self._signal_task: Optional[asyncio.Task] = None

    async def connect(self):
        """
        Handle new WebSocket connection with comprehensive validation.
        """
        try:
            # Authenticate and validate user
            await self.validate_user()


            # Initialize signal manager with multi-symbol support
            self.manager = SignalManager(
                symbols=self.symbols,
                timeframe=mt5.TIMEFRAME_M15,  # Configurable timeframe
                max_positions=10
            )
            self._setup_algorithms()

            # Accept connection and start signal generation
            await self.accept()
            self._signal_task = asyncio.create_task(self._generate_signals())

        except Exception as e:
            logger.error(f"Connection initialization error: {e}")
            await self.close(code=4001)


    async def validate_user(self):
        """
        Comprehensive user authentication validation.

        Raises:
            PermissionError: If user is not authenticated
        """
        if not self.scope['user'].is_authenticated:
            raise PermissionError("Unauthorized WebSocket access")


    def _setup_algorithms(self):
        """
        Configure multiple signal generation algorithms.

        Extensible design allows easy algorithm addition/modification.
        """
        algorithms = [
            AligatorAlgorithm(),
            MHarrisSystematic(),
            NadayaraWatsonFullStrategy15Min()
        ]
        for algo in algorithms:
            self.manager.add_algorithm(algo)

    async def _generate_signals(self):
        """
        Continuous signal generation with adaptive error handling.

        Implements:
        - Persistent signal generation
        - Error recovery mechanism
        - Configurable interval between signal generations
        """
        try:
            while True:
                signals = await self._fetch_signals()
                await self._broadcast_signals(signals)
                await asyncio.sleep(self.SIGNAL_INTERVAL)
        except asyncio.CancelledError:
            logger.info("Signal generation task cancelled")
        except Exception as e:
            logger.error(f"Critical signal generation failure: {e}")
            # Exponential backoff or reconnection strategy could be implemented here
            await asyncio.sleep(self.ERROR_WAIT_INTERVAL)

    async def _fetch_signals(self) -> Dict[str, Dict[str, Any]]:
        """
        Fetch signals for all symbols with detailed trade calculations.

        Returns:
            Dictionary of signals with trade details
        """
        signals = await self.manager.get_signals()
        return {
            symbol: self._calculate_trade_details(signal)
            for symbol, signal in signals.items()
        }

    def _calculate_trade_details(self, signal: str) -> Dict[str, Any]:
        """
        Generate comprehensive trade details based on signal.

        Args:
            signal (str): Trading signal ('buy', 'sell', 'hold')

        Returns:
            Dictionary with trade parameters
        """
        if signal == 'hold':
            return {
                'signal': 'hold',
                'entry_price': None,
                'sl': None,
                'tp': None
            }

        # Retrieve latest close price (simplified, replace with actual data retrieval)
        entry_price = self.manager.data_handlers[self.symbols[0]].get_data()["Close"].iloc[-1]

        trade_details = {
            'signal': signal,
            'entry_price': entry_price
        }

        perc = self.TRADE_PERCENTAGE
        if signal == "buy":
            trade_details.update({
                'sl': entry_price - entry_price * perc,
                'tp': entry_price + entry_price * perc * self.TPSL_RATIO
            })
        elif signal == "sell":
            trade_details.update({
                'sl': entry_price + entry_price * perc,
                'tp': entry_price - entry_price * perc * self.TPSL_RATIO
            })

        return trade_details

    async def _broadcast_signals(self, signals: Dict[str, Dict[str, Any]]):
        """
        Broadcast signals to connected WebSocket client.

        Implements:
        - Safe signal serialization
        - Error-resistant broadcasting
        """
        try:
            await self.send(text_data=json.dumps(signals))
        except Exception as e:
            logger.error(f"Signal broadcasting error: {e}")

    async def disconnect(self, close_code):
        """
        Graceful WebSocket disconnection handling.

        Ensures:
        - Signal generation task cancellation
        - Logging of disconnection reason
        """
        if self._signal_task:
            self._signal_task.cancel()
        logger.info(f"WebSocket connection closed: {close_code}")