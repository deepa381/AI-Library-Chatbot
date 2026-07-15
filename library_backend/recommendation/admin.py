from django.contrib import admin
from .models import RecommendationMetadata, SimilarBook, RecommendationHistory

@admin.register(RecommendationMetadata)
class RecommendationMetadataAdmin(admin.ModelAdmin):
    list_display = ("book", "difficulty_level", "reading_level", "created_at", "updated_at")
    search_fields = ("book__title", "themes", "keywords", "mood")

@admin.register(SimilarBook)
class SimilarBookAdmin(admin.ModelAdmin):
    list_display = ("book", "similar_book", "similarity_score", "rank", "created_at")
    search_fields = ("book__title", "similar_book__title")
    list_filter = ("rank",)


@admin.register(RecommendationHistory)
class RecommendationHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "query_preview", "created_at")
    search_fields = ("user__username", "query")
    list_filter = ("user",)
    readonly_fields = ("created_at", "updated_at")

    def query_preview(self, obj):
        return obj.query[:80]
    query_preview.short_description = "Query Preview"
