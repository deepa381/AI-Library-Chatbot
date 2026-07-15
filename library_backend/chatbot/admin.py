from django.contrib import admin
from .models import ChatbotMetadata, ChatSession, ChatMessage

@admin.register(ChatbotMetadata)
class ChatbotMetadataAdmin(admin.ModelAdmin):
    list_display = ("book", "short_ai_summary", "created_at", "updated_at")
    search_fields = ("book__title", "short_ai_summary", "long_ai_summary")


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "session_id", "title", "created_at", "updated_at")
    search_fields = ("user__username", "title")
    list_filter = ("user",)
    readonly_fields = ("session_id", "created_at", "updated_at")


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("session", "sender", "content_preview", "created_at")
    search_fields = ("session__session_id", "content")
    list_filter = ("sender",)

    def content_preview(self, obj):
        return obj.content[:80]
    content_preview.short_description = "Content Preview"
