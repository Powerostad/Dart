from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from apps.support.models import SupportThread, SupportMessage
from apps.support.serializers import SupportThreadSerializer, SupportMessageSerializer
from django.shortcuts import get_object_or_404
from utils.custom_smtp_server import CustomSMTPServer


class CreateSupportThreadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        thread_data = request.data
        thread_data['user'] = request.user.id
        serializer = SupportThreadSerializer(data=thread_data)
        if serializer.is_valid():
            thread = serializer.save()
            # Add initial message
            initial_message_data = {
                'thread': thread.id,
                'sender': request.user.id,
                'content': thread_data.get('content'),
                'is_response': False
            }
            message_serializer = SupportMessageSerializer(data=initial_message_data)
            if message_serializer.is_valid():
                message_serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(message_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ListSupportThreadsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.is_staff:
            threads = SupportThread.objects.all()
        else:
            threads = SupportThread.objects.filter(user=request.user)
        serializer = SupportThreadSerializer(threads, many=True)
        return Response(serializer.data)

class AddSupportMessageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, thread_id):
        # Fetch the thread and verify permissions
        thread = get_object_or_404(SupportThread, id=thread_id)
        if request.user != thread.user and not request.user.is_staff:
            return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)

        # Prepare the data for the serializer
        message_data = {
            'thread': thread.id,
            'sender': request.user.id,
            'content': request.data.get('content'),
            'is_response': request.user.is_staff
        }
        serializer = SupportMessageSerializer(data=message_data)

        # Validate and save the message
        if serializer.is_valid():
            message = serializer.save()
            thread.updated_at = message.sent_at  # Update the thread's timestamp
            thread.save()

            # Send email notification if it's a staff response
            if request.user.is_staff:
                self._send_notification_email(thread)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _send_notification_email(self, thread):
        """Sends an email notification to the user about the new response."""
        smtp_server = CustomSMTPServer()
        email_subject = f"Response to Your Support Query: {thread.title}"
        email_body = (
            f"Hello {thread.user.username},\n\n"
            f"You have a new response to your support message: '{thread.title}'.\n"
            f"Please log in to view the details.\n\n"
            f"Best regards,\nSupport Team"
        )
        smtp_server.send_email(thread.user.email, email_subject, email_body)
    

class ListThreadMessagesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, thread_id):
        thread = get_object_or_404(SupportThread, id=thread_id)
        if request.user != thread.user and not request.user.is_staff:
            return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)
        messages = thread.messages.all()
        serializer = SupportMessageSerializer(messages, many=True)
        return Response(serializer.data)
    
# User views their threads
class UserSupportThreadsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        threads = SupportThread.objects.filter(user=request.user)
        serializer = SupportThreadSerializer(threads, many=True)
        return Response(serializer.data)    
