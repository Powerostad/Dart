from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.chatbot.models import Conversation
from apps.chatbot.serializers import ConversationSerializer


class ChatbotHistoryView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ConversationSerializer

    def get(self, request):
        user = request.user
        user_all_conversations = Conversation.objects.filter(user=user)
        serializer = self.serializer_class(user_all_conversations, many=True)
        response = [
            {"conversation_id": conv["id"], "title": conv["title"]} for conv in serializer.data
        ]
        return Response(response, status=status.HTTP_200_OK)



