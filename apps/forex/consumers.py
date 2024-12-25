import asyncio
import datetime
import json
import logging
from typing import Set, Optional, Dict
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.exceptions import DenyConnection
from utils.algorithms.algorithms import AligatorAlgorithm, MHarrisSystematic, NadayaraWatsonFullStrategy15Min
from utils.controllers.signal import SignalController

logger = logging.getLogger(__name__)


class TradingConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.signal_controller: Optional[SignalController] = None
        self.subscribed_symbols: Set[str] = set()
        self.connected = False
        self.signal_task = None
        self.last_signals: Dict = {}  # Cache for last signals
        self.SIGNAL_CHECK_INTERVAL = 5  # seconds

    async def connect(self):
        """
        Handle WebSocket connection with authentication
        """
        try:
            # Verify authentication
            if self.scope["user"].is_anonymous:
                raise DenyConnection("Authentication required")

            self.user = self.scope["user"]

            # Initialize signal controller with default settings
            # You might want to customize these based on user preferences
            default_algorithms = [
                AligatorAlgorithm(),
                NadayaraWatsonFullStrategy15Min(),
                MHarrisSystematic()
            ]
            default_timeframes = ["15m", "1h", "4h"]  # Customize as needed

            self.signal_controller = await SignalController.create(
                symbols=[],  # Initially empty, will be populated on subscription
                timeframes=default_timeframes,
                algorithms=default_algorithms
            )

            self.connected = True
            await self.accept()

            # Send initial available symbols
            available_symbols = await self.signal_controller.available_symbols()
            await self.send(json.dumps({
                "type": "available_symbols",
                "symbols": available_symbols
            }))

            self.signal_task = asyncio.create_task(self.monitor_signals())
            logger.info(f"WebSocket connection established for user {self.user.id}")
        except Exception as e:
            raise e
            logger.error(f"Connection error: {str(e)}")
            raise DenyConnection(str(e))

    async def disconnect(self, close_code):
        """
        Clean up subscriptions and connections
        """
        try:
            # Cancel signal monitoring task
            if self.signal_task:
                self.signal_task.cancel()
                try:
                    await self.signal_task
                except asyncio.CancelledError:
                    pass

            # Unsubscribe from all symbol groups
            for symbol in self.subscribed_symbols:
                await self.channel_layer.group_discard(
                    f"symbol_{symbol}",
                    self.channel_name
                )
            self.subscribed_symbols.clear()
            self.connected = False
            logger.info(f"WebSocket disconnected for user {self.user.id}")

        except Exception as e:
            logger.error(f"Disconnection error: {str(e)}")

    async def receive(self, text_data):
        """
        Handle incoming WebSocket messages
        """
        try:
            data = json.loads(text_data)
            message_type = data.get("type")

            handlers = {
                "subscribe": self.handle_subscribe,
                "unsubscribe": self.handle_unsubscribe,
                "request_signals": self.handle_signal_request
            }

            handler = handlers.get(message_type)
            if handler:
                await handler(data)
            else:
                await self.send(json.dumps({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                }))

        except json.JSONDecodeError:
            await self.send(json.dumps({
                "type": "error",
                "message": "Invalid JSON format"
            }))
        except Exception as e:
            raise e
            logger.error(f"Message handling error: {str(e)}")
            await self.send(json.dumps({
                "type": "error",
                "message": str(e)
            }))

    async def monitor_signals(self):
        """
        Periodically check for signal updates and broadcast changes
        """
        while self.connected:
            try:
                if self.subscribed_symbols:
                    signals = await self.signal_controller.generate_multi_timeframe_signals()

                    # Check if signals have changed
                    if signals != self.last_signals:
                        self.last_signals = signals

                        # Format signals for transmission
                        formatted_signals = {
                            symbol: [signal.to_dict() for signal in symbol_signals]
                            for symbol, symbol_signals in signals.items()
                        }

                        # Send to client
                        if self.connected:  # Double-check connection
                            await self.send(json.dumps({
                                "type": "signals",
                                "data": formatted_signals,
                                "timestamp": datetime.datetime.now().isoformat()
                            }))
                            logger.debug(f"Signals broadcasted to user {self.user.id}")

                await asyncio.sleep(self.SIGNAL_CHECK_INTERVAL)

            except asyncio.CancelledError:
                raise
            except Exception as e:
                raise e
                logger.error(f"Signal monitoring error: {str(e)}")
                await asyncio.sleep(self.SIGNAL_CHECK_INTERVAL)

    async def handle_subscribe(self, data):
        """
        Handle symbol subscription requests
        """
        symbols = data.get("symbols", [])
        if not symbols:
            await self.send(json.dumps({
                "type": "error",
                "message": "No symbols provided for subscription"
            }))
            return

        # Verify symbols are valid
        available_symbols = await self.signal_controller.available_symbols()
        invalid_symbols = set(symbols) - set(available_symbols)
        if invalid_symbols:
            await self.send(json.dumps({
                "type": "error",
                "message": f"Invalid symbols: {', '.join(invalid_symbols)}"
            }))
            return

        # Subscribe to new symbols
        for symbol in symbols:
            if symbol not in self.subscribed_symbols:
                await self.channel_layer.group_add(
                    f"symbol_{symbol}",
                    self.channel_name
                )
                self.subscribed_symbols.add(symbol)

        # Update signal controller symbols
        self.signal_controller.symbols = list(self.subscribed_symbols)

        # Force immediate signal check
        if self.subscribed_symbols:
            signals = await self.signal_controller.generate_multi_timeframe_signals()
            if signals:
                formatted_signals = {
                    symbol: [signal.to_dict() for signal in symbol_signals]
                    for symbol, symbol_signals in signals.items()
                }
                await self.send(json.dumps({
                    "type": "signals",
                    "data": formatted_signals
                }))

        await self.send(json.dumps({
            "type": "subscription_update",
            "subscribed_symbols": list(self.subscribed_symbols)
        }))
        logger.info(f"User {self.user.id} subscribed to symbols: {symbols}")

    async def handle_unsubscribe(self, data):
        """
        Handle symbol unsubscription requests
        """
        symbols = data.get("symbols", [])
        for symbol in symbols:
            if symbol in self.subscribed_symbols:
                await self.channel_layer.group_discard(
                    f"symbol_{symbol}",
                    self.channel_name
                )
                self.subscribed_symbols.remove(symbol)

        # Update signal controller symbols
        self.signal_controller.symbols = list(self.subscribed_symbols)

        await self.send(json.dumps({
            "type": "subscription_update",
            "subscribed_symbols": list(self.subscribed_symbols)
        }))

    async def handle_signal_request(self, data):
        """
        Handle requests for trading signals
        """
        if not self.subscribed_symbols:
            await self.send(json.dumps({
                "type": "error",
                "message": "No symbols subscribed"
            }))
            return

        try:
            signals = await self.signal_controller.generate_multi_timeframe_signals()
            await self.send(json.dumps({
                "type": "signals",
                "data": {
                    symbol: [signal.to_dict() for signal in symbol_signals]
                    for symbol, symbol_signals in signals.items()
                }
            }))
        except Exception as e:
            raise e
            logger.error(f"Signal generation error: {str(e)}")
            await self.send(json.dumps({
                "type": "error",
                "message": "Error generating signals"
            }))

    async def signal_update(self, event):
        """
        Handle signal updates from other parts of the system
        """
        if not self.connected:
            return

        await self.send(json.dumps({
            "type": "signal_update",
            "data": event["data"]
        }))