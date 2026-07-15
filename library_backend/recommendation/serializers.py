from rest_framework import serializers
from recommendation.models import RecommendationHistory
from books.serializers import BookSerializer

class RecommendationHistorySerializer(serializers.ModelSerializer):
    recommended_books = BookSerializer(many=True, read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = RecommendationHistory
        fields = ['id', 'username', 'query', 'response', 'recommended_books', 'created_at']
        read_only_fields = ['id', 'username', 'response', 'recommended_books', 'created_at']


class RecommendationQuerySerializer(serializers.Serializer):
    query = serializers.CharField(
        required=True,
        help_text="Query description of preferences or mood to get book recommendations."
    )
