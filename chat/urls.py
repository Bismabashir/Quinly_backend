from django.urls import path
from .views import create_conversation, get_messages, user_conversations

urlpatterns = [
    path("conversations/", create_conversation, name="create_conversation"),
    path("user-conversations/", user_conversations, name="user_conversations"),
    path("messages/<uuid:conversation_id>/", get_messages, name="get_messages"),
]
