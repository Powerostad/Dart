import asyncio
import json
from urllib.parse import parse_qs
from rest_framework_simplejwt.tokens import AccessToken
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model

from utils.algorithms.algorithms import AligatorAlgorithm, NadayaraWatsonFullStrategy15Min, MHarrisSystematic
from utils.signal_manager.signal_manager import SignalManager

User = get_user_model()


class SignalConsumer(AsyncWebsocketConsumer):
    async def connect(self):

        self.symbol = self.scope['url_route']['kwargs']['symbol'].upper()
        self.manager = SignalManager(self.symbol)

        self.manager.add_algorithm(AligatorAlgorithm())
        self.manager.add_algorithm(MHarrisSystematic())
        self.manager.add_algorithm(NadayaraWatsonFullStrategy15Min())

        # Create a unique group name based on the symbol
        self.group_name = f"signals_{self.symbol}"

        if self.scope['user'].is_authenticated:
            # Join the group
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )

            # Accept the WebSocket connection
            await self.accept()
            print("Accept")
            # Start the signal loop in a separate task
            await asyncio.create_task(self.signal_loop())
        else:
            await self.close(code=4001)

    async def disconnect(self, close_code):
        # Remove the consumer from the group when disconnected
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        print(f"Connection closed with code: {close_code}")

    async def signal_loop(self):
        perc = 0.02
        TPSLRatio = 1.5

        while True:
            try:
                loop = asyncio.get_event_loop()
                signal = await loop.run_in_executor(None, self.manager.get_signal)
                print("Hold")

                message = {
                    'signal': "hold",
                    'entry_price': None
                }
                if signal != 'hold':
                    entry_price = self.manager.data_handler.get_data()["Close"].iloc[-1]
                    message = {
                        'signal': signal,
                        'entry_price': entry_price
                    }

                    # Calculate trade details based on signal
                    if signal == "buy":
                        stop_loss = entry_price - entry_price * perc
                        target_point = entry_price + entry_price * perc * TPSLRatio
                        message.update({'sl': stop_loss, 'tp': target_point})

                    elif signal == "sell":
                        sl1 = entry_price + entry_price * perc
                        tp1 = entry_price - entry_price * perc * TPSLRatio
                        message.update({'sl': sl1, 'tp': tp1})

                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        "type": "chat.message",
                        "message": message
                    }
                )

                await asyncio.sleep(60)
            except Exception as e:
                raise e
                await self.base_send({'error': str(e)})
                await asyncio.sleep(60)

    async def chat_message(self, event):
        message = event["message"]
        await self.send(text_data=json.dumps(message))
