from django.urls import path
from .views import create_conversation, get_messages, user_conversations, dashboard_stats

urlpatterns = [
    path("conversations/", create_conversation, name="create_conversation"),
    path("dashboard-stats/", dashboard_stats, name="dashboard_stats"),
    path("user-conversations/", user_conversations, name="user_conversations"),
    path("messages/<uuid:conversation_id>/", get_messages, name="get_messages"),
]
