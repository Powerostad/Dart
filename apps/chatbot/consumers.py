import json
from typing import List, Dict, AsyncGenerator

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from groq import AsyncGroq
from django.contrib.auth import get_user_model
from logging import getLogger

from apps.chatbot.models import Conversation, ConversationMessage

logger = getLogger(__name__)
User = get_user_model()


class AIChatbotConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for AI chatbot with comprehensive conversation tracking
    """

    async def connect(self):
        """
        Handle new WebSocket connection
        """
        # Ensure user is authenticated
        if not self.scope['user'].is_authenticated:
            await self.close()
            return

        # Accept the WebSocket connection
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        """
        Handle incoming WebSocket messages
        """
        try:
            # Parse the incoming JSON data
            data = json.loads(text_data)
            message = data.get('message')
            conversation_id = data.get('conversation_id')

            # Validate message
            if not message:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'No message provided'
                }))
                return

            # Ensure conversation exists or create new
            conversation = await self.get_or_create_conversation(
                conversation_id,
                self.scope['user']
            )

            # Save user message
            await self.save_message(
                conversation,
                'user',
                message
            )

            # Initialize Groq client
            client = AsyncGroq(api_key=settings.GROQ_API_KEY)

            # Retrieve conversation history
            chat_history = await self.get_conversation_history(conversation)

            # Send typing indicator
            await self.send(text_data=json.dumps({
                'type': 'typing_start'
            }))

            # Prepare to collect full response for saving
            full_response = []

            # Stream the AI response
            async for chunk in await self.stream_ai_response(client, chat_history, message):
                # Send each chunk
                await self.send(text_data=json.dumps({
                    'type': 'stream',
                    'content': chunk
                }))

                # Collect full response
                full_response.append(chunk)

            # Save AI response
            await self.save_message(
                conversation,
                'assistant',
                ''.join(full_response)
            )

            # End of streaming
            await self.send(text_data=json.dumps({
                'type': 'stream_end',
                'conversation_id': str(conversation.id)
            }))

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            logger.error(f"Error in WebSocket: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    @database_sync_to_async
    def get_or_create_conversation(
            self,
            conversation_id: str,
            user: User
    ) -> Conversation:
        """
        Get an existing conversation or create a new one

        :param conversation_id: Optional existing conversation ID
        :param user: Authenticated user
        :return: Conversation instance
        """
        if conversation_id:
            try:
                return Conversation.objects.get(
                    id=conversation_id,
                    user=user
                )
            except Conversation.DoesNotExist:
                pass

        # Create new conversation
        return Conversation.objects.create(
            user=user,
            title="New Conversation"
        )

    @database_sync_to_async
    def save_message(
            self,
            conversation: Conversation,
            role: str,
            content: str
    ):
        """
        Save a message to the conversation

        :param conversation: Conversation instance
        :param role: Message role (user/assistant)
        :param content: Message content
        """
        ConversationMessage.objects.create(
            conversation=conversation,
            role=role,
            content=content
        )

    @database_sync_to_async
    def get_conversation_history(
            self,
            conversation: Conversation,
            limit: int = 10
    ) -> List[Dict[str, str]]:
        """
        Retrieve recent conversation history

        :param conversation: Conversation instance
        :param limit: Number of recent messages to retrieve
        :return: List of message dictionaries
        """
        # Retrieve recent messages, limited to last 10
        messages = conversation.messages.order_by('-created_at')[:limit]

        # Prepare messages in Groq-compatible format
        history = []

        # Add system message
        history.append({
            "role": "system",
            "content": "You are a helpful AI assistant. Provide clear and concise responses."
        })

        # Add conversation messages in chronological order
        for message in reversed(list(messages)):
            history.append({
                "role": message.role,
                "content": message.content
            })

        return history

    async def stream_ai_response(
            self,
            client: AsyncGroq,
            chat_history: List[Dict[str, str]],
            new_message: str
    ) -> AsyncGenerator[str, None]:
        """
        Stream AI response using Groq library

        :param client: Async Groq client
        :param chat_history: Previous conversation context
        :param new_message: Latest user message
        :return: Async generator of response chunks
        """
        # Prepare full message list
        messages = chat_history + [
            {
                "role": "user",
                "content": new_message
            }
        ]

        # Stream completion
        stream = await client.chat.completions.create(
            model="mixtral-8x7b-32768",  # or another Groq model
            messages=messages,
            stream=True
        )

        # Generate chunks
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
