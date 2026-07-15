from rest_framework import serializers
from chatbot.models import ChatSession, ChatMessage
from books.serializers import BookSerializer

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'sender', 'content', 'created_at']
        read_only_fields = ['id', 'created_at']


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = ChatSession
        fields = ['id', 'session_id', 'title', 'messages', 'created_at', 'updated_at']
        read_only_fields = ['id', 'session_id', 'created_at', 'updated_at']


class ChatInputSerializer(serializers.Serializer):
    message = serializers.CharField(
        required=True,
        help_text="The message or query to send to the chatbot."
    )
    session_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text="Optional UUID of an existing chat session to continue the conversation."
    )


class SearchQuerySerializer(serializers.Serializer):
    q = serializers.CharField(
        required=True,
        help_text="Search query string."
    )
