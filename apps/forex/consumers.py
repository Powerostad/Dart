import asyncio
import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from utils.controllers.metatrader import AsyncMT5Controller
from .models import Signal

logger = logging.getLogger(__name__)


class MT5DataConsumer(AsyncWebsocketConsumer):
    """Consumer for streaming MetaTrader5 data to front-end."""

    async def connect(self):
        """Handle WebSocket connection."""
        # Get symbol from URL route
        self.symbol = self.scope['url_route']['kwargs'].get('symbol')
        self.timeframe = self.scope['url_route']['kwargs'].get('timeframe', '5m')

        if not self.symbol:
            await self.close(code=4000)
            return

        # Join symbol-specific group
        self.group_name = f"mt5_data_{self.symbol}_{self.timeframe}"
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

        self.data_task = asyncio.create_task(self.send_data_periodic())

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Cancel the periodic data task
        if hasattr(self, 'data_task'):
            self.data_task.cancel()

        # Leave the group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Handle messages from WebSocket."""
        try:
            data = json.loads(text_data)
            command = data.get('command')

            if command == 'get_historical':
                # Fetch historical data
                lookback = data.get('lookback', 300)
                await self.send_historical_data(lookback)
            elif command == 'update_timeframe':
                # Update timeframe
                new_timeframe = data.get('timeframe', '15m')
                # Leave old group
                await self.channel_layer.group_discard(
                    self.group_name,
                    self.channel_name
                )
                # Join new group
                self.timeframe = new_timeframe
                self.group_name = f"mt5_data_{self.symbol}_{self.timeframe}"
                await self.channel_layer.group_add(
                    self.group_name,
                    self.channel_name
                )
                # Send confirmation
                await self.send(text_data=json.dumps({
                    'type': 'timeframe_updated',
                    'timeframe': self.timeframe
                }))
        except json.JSONDecodeError:
            pass

    async def send_historical_data(self, lookback=300):
        """Send historical data for the symbol."""
        try:
            mt5_controller = await AsyncMT5Controller.get_instance()
            data = await mt5_controller.get_historical_data_candles(
                self.symbol,
                self.timeframe,
                lookback
            )

            if data is not None and not data.empty:
                # Convert DataFrame to JSON-serializable format
                candles = []
                for idx, row in data.iterrows():
                    candle = {
                        'time': idx.isoformat(),
                        'open': row['open'],
                        'high': row['high'],
                        'low': row['low'],
                        'close': row['close'],
                        'volume': row['tick_volume']
                    }
                    candles.append(candle)

                await self.send(text_data=json.dumps({
                    'type': 'historical_data',
                    'symbol': self.symbol,
                    'timeframe': self.timeframe,
                    'candles': candles
                }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    async def send_data_periodic(self):
        """Periodically send real-time data updates."""
        try:
            while True:
                mt5_controller = await AsyncMT5Controller.get_instance()

                # Get latest candle data
                data = await mt5_controller.get_historical_data_candles(
                    self.symbol,
                    self.timeframe,
                    1  # Just the latest candle
                )

                if data is not None and not data.empty:
                    # Get the latest row
                    latest = data.iloc[-1]

                    # Create candle object
                    candle = {
                        'time': data.index[-1].isoformat(),
                        'open': float(latest['open']),
                        'high': float(latest['high']),
                        'low': float(latest['low']),
                        'close': float(latest['close']),
                        'volume': int(latest['tick_volume'])
                    }

                    # Get any active signals for this symbol
                    signals = await self.get_active_signals(self.symbol)

                    # Send to the group
                    await self.channel_layer.group_send(
                        self.group_name,
                        {
                            'type': 'send_update',
                            'symbol': self.symbol,
                            'candle': candle,
                            'signals': signals
                        }
                    )

                # Wait appropriate interval based on timeframe
                if self.timeframe == '1m':
                    await asyncio.sleep(5)  # Update every 5 seconds for 1-minute charts
                elif self.timeframe == '5m':
                    await asyncio.sleep(15)  # Every 15 seconds for 5-minute charts
                else:
                    await asyncio.sleep(30)  # Default 30 seconds for other timeframes

        except asyncio.CancelledError:
            # Task was cancelled, clean up
            pass
        except Exception as e:
            # Send error to client
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    @database_sync_to_async
    def get_active_signals(self, symbol):
        """Get active signals for the given symbol."""
        signals = Signal.objects.filter(
            symbol=symbol,
            status="ACTIVE"
        ).values()

        return list(signals)

    async def send_update(self, event):
        """Send update to WebSocket."""
        # Forward the update to the WebSocket
        await self.send(text_data=json.dumps({
            'type': 'candle_update',
            'symbol': event['symbol'],
            'candle': event['candle'],
            'signals': event.get('signals', [])
        }))
