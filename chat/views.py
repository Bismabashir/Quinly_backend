from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Conversation, Message
from .serializers import MessageSerializer, ConversationSerializer


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_conversation(request):
    conversation = Conversation.objects.create(user=request.user)
    return Response({"conversation_id": conversation.id}, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_messages(request, conversation_id):
    messages = Message.objects.filter(conversation_id=conversation_id).order_by("created_at")
    return Response({"messages": MessageSerializer(messages, many=True).data}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_conversations(request):
    user = request.user
    messages = Conversation.objects.filter(user_id=user.id).order_by("-created_at")
    return Response({"conversations": ConversationSerializer(messages, many=True).data}, status=status.HTTP_200_OK)
