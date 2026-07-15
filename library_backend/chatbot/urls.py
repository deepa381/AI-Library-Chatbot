from django.urls import path
from chatbot.views import (
    ChatView,
    ChatHistoryListView,
    ChatHistoryDetailView,
    SearchView
)

app_name = 'chatbot'

urlpatterns = [
    path('chat/', ChatView.as_view(), name='chat'),
    path('chat/history/', ChatHistoryListView.as_view(), name='chat-history-list'),
    path('chat/history/<uuid:session_id>/', ChatHistoryDetailView.as_view(), name='chat-history-detail'),
    path('search/', SearchView.as_view(), name='search'),
]
