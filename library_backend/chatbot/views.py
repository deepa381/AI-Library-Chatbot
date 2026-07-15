from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.core.exceptions import ValidationError

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from chatbot.models import ChatSession
from chatbot.serializers import (
    ChatSessionSerializer,
    ChatInputSerializer,
    SearchQuerySerializer
)
from chatbot.services import ChatbotEngine, SearchService
from books.serializers import BookSerializer


class ChatView(APIView):
    """
    POST /api/chat/
    Send a message to the AI chatbot. Creates a session if session_id is not provided,
    otherwise continues the existing session.
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        request_body=ChatInputSerializer,
        responses={
            200: openapi.Response(
                description="Success",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'session_id': openapi.Schema(type=openapi.TYPE_STRING, format='uuid'),
                        'session_title': openapi.Schema(type=openapi.TYPE_STRING),
                        'response': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: "Invalid input"
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = ChatInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        message = serializer.validated_data['message']
        session_id = serializer.validated_data.get('session_id')
        
        if session_id:
            try:
                session = ChatSession.objects.get(session_id=session_id, user=request.user)
            except (ChatSession.DoesNotExist, ValidationError):
                return Response(
                    {"error": "Chat session not found or does not belong to you."},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            session = ChatSession.objects.create(user=request.user)

        engine = ChatbotEngine()
        bot_response = engine.get_chatbot_response(request.user, session, message)

        return Response({
            "session_id": str(session.session_id),
            "session_title": session.title,
            "response": bot_response
        }, status=status.HTTP_200_OK)


class ChatHistoryListView(APIView):
    """
    GET /api/chat/history/
    Retrieve chat session history for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        responses={200: ChatSessionSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        sessions = ChatSession.objects.filter(user=request.user).prefetch_related('messages')
        serializer = ChatSessionSerializer(sessions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChatHistoryDetailView(APIView):
    """
    GET /api/chat/history/<session_id>/
    DELETE /api/chat/history/<session_id>/
    Retrieve or delete a specific chat session by session_id.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_session(self, request, session_id):
        try:
            return ChatSession.objects.get(session_id=session_id, user=request.user)
        except (ChatSession.DoesNotExist, ValidationError):
            return None

    @swagger_auto_schema(
        responses={
            200: ChatSessionSerializer(),
            404: "Session not found"
        }
    )
    def get(self, request, session_id, *args, **kwargs):
        session = self.get_session(request, session_id)
        if not session:
            return Response({"error": "Chat session not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ChatSessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        responses={
            204: "Session deleted successfully",
            404: "Session not found"
        }
    )
    def delete(self, request, session_id, *args, **kwargs):
        session = self.get_session(request, session_id)
        if not session:
            return Response({"error": "Chat session not found."}, status=status.HTTP_404_NOT_FOUND)
        session.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SearchView(APIView):
    """
    GET /api/search/
    Search for books across title, author, description, tags, keywords, mood etc.
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        query_serializer=SearchQuerySerializer,
        responses={200: BookSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        serializer = SearchQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        query_str = serializer.validated_data['q']
        results = SearchService.search_books(query_str, limit=10)
        
        book_serializer = BookSerializer(results, many=True)
        return Response(book_serializer.data, status=status.HTTP_200_OK)
