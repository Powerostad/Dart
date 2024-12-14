import json
from typing import List, Dict, AsyncGenerator
from logging import getLogger

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.contrib.auth import get_user_model

from apps.chatbot.models import Conversation, ConversationMessage
from groq import AsyncGroq

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
        user = self.scope['user']
        if not user.is_authenticated:
            logger.warning("Unauthorized connection attempt")
            await self.close()
            return

        logger.info(f"WebSocket connected for user: {user}")
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        """
        Handle incoming WebSocket messages
        """
        try:
            logger.debug(f"Received WebSocket data: {text_data}")
            data = json.loads(text_data)
            message = data.get('message')
            conversation_id = data.get('conversation_id')

            if not message:
                logger.warning("Received invalid message payload with no 'message' field")
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'No message provided'
                }))
                return

            logger.info(f"Processing message: {message} for conversation ID: {conversation_id}")
            conversation = await self.get_or_create_conversation(conversation_id, self.scope['user'], message)
            logger.info(f"Using conversation ID: {conversation.id}")

            await self.save_message(conversation, 'user', message)
            logger.debug(f"Saved user message: {message}")

            client = AsyncGroq(api_key=settings.GROQ_API_KEY)
            chat_history = await self.get_conversation_history(conversation)
            logger.debug(f"Retrieved conversation history: {chat_history}")

            await self.send(text_data=json.dumps({'type': 'typing_start'}))
            logger.info("Sent typing indicator to user")

            full_response = []

            async for chunk in self.stream_ai_response(client, chat_history, message):
                logger.debug(f"Streaming AI response chunk: {chunk}")
                await self.send(text_data=json.dumps({
                    'type': 'stream',
                    'content': chunk
                }))
                full_response.append(chunk)

            await self.save_message(conversation, 'assistant', ''.join(full_response))
            logger.info(f"AI response saved for conversation ID: {conversation.id}")

            await self.send(text_data=json.dumps({
                'type': 'stream_end',
                'conversation_id': str(conversation.id)
            }))
            logger.info("Sent stream end indicator to user")

        except json.JSONDecodeError as e:
            logger.error(f"JSONDecodeError: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'An unexpected error occurred. Please try again.'
            }))

    @database_sync_to_async
    def get_or_create_conversation(self, conversation_id: str, user: User, user_message: str) -> Conversation:
        logger.debug(f"Retrieving or creating conversation with ID: {conversation_id} for user: {user}")
        if conversation_id:
            try:
                return Conversation.objects.get(id=conversation_id, user=user)
            except Conversation.DoesNotExist:
                logger.info(f"Conversation with ID {conversation_id} not found. Creating a new one.")

        new_conversation = Conversation.objects.create(
            user=user,
            title=user_message[:20] if len(user_message) > 20 else user_message,
        )
        logger.info(f"Created new conversation with ID: {new_conversation.id}")
        return new_conversation

    @database_sync_to_async
    def save_message(self, conversation: Conversation, role: str, content: str):
        logger.debug(f"Saving message for conversation ID: {conversation.id}, role: {role}, content: {content}")
        ConversationMessage.objects.create(conversation=conversation, role=role, content=content)
        logger.info(f"Message saved for conversation ID: {conversation.id}, role: {role}")

    @database_sync_to_async
    def get_conversation_history(self, conversation: Conversation, limit: int = 10) -> List[Dict[str, str]]:
        logger.debug(f"Retrieving last {limit} messages for conversation ID: {conversation.id}")
        messages = conversation.messages.order_by('-created_at')[:limit]

        history = [{"role": "system", "content": "You are a helpful AI assistant. Provide clear and concise responses."}]
        history += [{"role": message.role, "content": message.content} for message in reversed(list(messages))]
        logger.info(f"Retrieved conversation history for conversation ID: {conversation.id}")
        return history

    async def stream_ai_response(self, client: AsyncGroq, chat_history: List[Dict[str, str]], new_message: str) -> AsyncGenerator[str, None]:
        logger.debug("Streaming AI response")
        system_message = {
            "role": "system",
            "content": "You are a specialized finance and trading educational assistant. Your primary purpose is to help users understand and learn about trading and finance concepts. Guidelines:\n1. Only discuss topics related to finance and trading\n2. Provide educational explanations and insights\n3. Never give financial predictions or investment advice\n4. If asked about predictions, explain that you cannot provide them\n5. Respond in Persian when the user communicates in Persian"
        }
        messages = [system_message] + chat_history + [{"role": "user", "content": new_message}]
        stream = await client.chat.completions.create(model="gemma2-9b-it", messages=messages, stream=True)

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
