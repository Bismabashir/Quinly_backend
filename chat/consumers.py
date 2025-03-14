import json
from channels.generic.websocket import AsyncWebsocketConsumer
from urllib.parse import parse_qs
from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from user.models import User
from .models import Conversation, Message
from .openai_utils import generate_ai_response
from .utils import analyze_sentiment, detect_topic


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        query_string = parse_qs(self.scope["query_string"].decode())
        token = query_string.get("token", [None])[0]

        if not token:
            await self.close(code=403)
            return

        self.user = await self.get_user_from_token(token)

        if not self.user or self.user.is_anonymous:
            await self.close(code=403)
            return

        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]

        self.conversation = await self.get_conversation(self.conversation_id)
        if not self.conversation:
            await self.close(code=403)
            return

        self.room_group_name = f"chat_{self.conversation_id}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # async def receive(self, text_data):
    #     data = json.loads(text_data)
    #     user_message = data.get("message")
    #     print(user_message)
    #     is_premium = data.get("is_premium", False)

    #     if not user_message:
    #         await self.send(text_data=json.dumps({"error": "Message field is required."}))
    #         return

    #     sentiment = analyze_sentiment(user_message)
    #     topic = detect_topic(user_message)

    #     is_emergency = sentiment.lower() == "critical"

    #     bot_response = generate_ai_response(user_message, topic, sentiment, is_premium)
    #     print("Bottt",bot_response)
       #######################################################
        # await self.channel_layer.group_send(
        #     self.room_group_name,
        #     {
        #         "type": "chat_message",
        #         "sender": "user",
        #         "user_message": user_message,
        #         "bot_response": None,  # No bot response yet
        #         "sentiment": sentiment,
        #         "topic": topic,
        #         "is_emergency": is_emergency,
        #     }
        
        # )
        ###########################################################
        # await self.channel_layer.group_send(
        #     self.room_group_name,
        #     {
        #         "type": "chat_message",
        #         "user_message": None,
        #         "bot_response": bot_response,
        #         "sentiment": None,
        #         "topic": None,
        #         "is_emergency": is_emergency,
        #     }
        # )

        # print("Messages forwarded")

        # conversation = await self.get_conversation(self.conversation_id)
        # await self.save_message(conversation, "user", user_message, None, sentiment, topic, is_emergency)
        # await self.save_message(conversation, "bot", None, bot_response, None, None, False)
    async def receive(self, text_data):
        data = json.loads(text_data)
        user_message = data.get("message")
        is_premium = data.get("is_premium", False)

        if not user_message:
            await self.send(text_data=json.dumps({"error": "Message field is required."}))
            return

        sentiment = analyze_sentiment(user_message)
        topic = detect_topic(user_message)

        #  Check for grooming or self-harm risk
        is_emergency = sentiment.lower() == "critical" or topic.lower() in ["grooming", "self-harm", "abuse"]

        # Generate AI response
        bot_response = await generate_ai_response(user_message, topic, sentiment, is_premium, self.conversation_id)

        #  **Emergency Handling for Sensitive Topics**
        if topic.lower() == "grooming":
            bot_response = (
                " This is serious. If someone is asking for pictures or making you uncomfortable online, **DO NOT** respond to them. "
                " **Block & report them immediately.** "
                "Here’s how you can report online abuse: [CEOP](https://www.ceop.police.uk), [NSPCC](https://www.nspcc.org.uk/), or talk to [Childline](https://www.childline.org.uk/). "
                "You are not alone. Do you need more guidance on handling this?"
            )

        elif topic.lower() == "self-harm":
            bot_response = (
                "💙 I'm really sorry you're feeling this way. You’re not alone, and there are people who care about you. "
                "If you need someone to talk to, you can text **SHOUT to 85258** or call **Samaritans at 116 123** (available 24/7). "
                "If you're in immediate danger, please **call 999**. Would you like to talk about what’s on your mind?"
            )

        # Send response
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "user_message": None,
                "bot_response": bot_response,
                "sentiment": sentiment,
                "topic": topic,
                "is_emergency": is_emergency,
            }
        )

        # Save messages to database
        conversation = await self.get_conversation(self.conversation_id)
        await self.save_message(conversation, "user", user_message, None, sentiment, topic, is_emergency)
        await self.save_message(conversation, "bot", None, bot_response, None, None, is_emergency)
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "sender": "bot",
            "user_message": event["user_message"],
            "bot_response": event["bot_response"],
            "sentiment": event["sentiment"],
            "topic": event["topic"],
            "is_emergency": event["is_emergency"],
        }))

    @database_sync_to_async
    def get_user_from_token(self, token):
        try:
            decoded_token = AccessToken(token)
            user_id = decoded_token["user_id"]
            return User.objects.get(id=user_id)
        except Exception:
            return AnonymousUser()

    @database_sync_to_async
    def get_conversation(self, conversation_id):
        try:
            return Conversation.objects.get(id=conversation_id, user=self.user)
        except Conversation.DoesNotExist:
            return None

    async def save_message(self, conversation, sender, user_message, bot_response, sentiment, topic, is_emergency):
        await Message.objects.acreate(
            conversation=conversation,
            sender=sender,
            user_message=user_message,
            bot_response=bot_response,
            sentiment=sentiment,
            topic=topic,
            is_emergency=is_emergency
        )
