from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from recommendation.serializers import RecommendationQuerySerializer
from books.serializers import BookSerializer
from chatbot.services import RecommendationService



class RecommendView(APIView):
    """
    POST /api/recommend/
    Request recommendations based on preferences, mood, tags, etc.
    Returns ranked books and an AI generated explanation/reasoning.
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        request_body=RecommendationQuerySerializer,
        responses={
            200: openapi.Response(
                description="Success",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'response': openapi.Schema(type=openapi.TYPE_STRING, description="AI ranked explanation"),
                        'books': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_OBJECT),
                            description="Ranked candidate books"
                        ),
                    }
                )
            ),
            400: "Invalid input"
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = RecommendationQuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        query = serializer.validated_data['query']
        service = RecommendationService()
        
        response_text, candidates = service.get_recommendations(query, request.user)
        
        book_serializer = BookSerializer(candidates, many=True)
        return Response({
            "response": response_text,
            "books": book_serializer.data
        }, status=status.HTTP_200_OK)
