from .system_message import SYSTEM_MESSAGE
import os
from dotenv import load_dotenv
from openai import OpenAI
from django.conf import settings
from .models import Message # added function from models file
from channels.db import database_sync_to_async

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

@database_sync_to_async
def get_last_messages(conversation_id, limit=6):
    messages = Message.objects.filter(conversation_id=conversation_id).order_by("-created_at")[:limit]
    return "\n".join([f"User: {msg.user_message}\nBot: {msg.bot_response}" for msg in messages if msg.user_message])

async def generate_ai_response(user_message, topic, sentiment, is_premium, conversation_id):
   
    model = "gpt-4o" if is_premium else "gpt-3.5-turbo"
    extra_instruction = ""

    if sentiment == "critical":
        extra_instruction = (
            "This user is in a **critical emotional state**. Use **high empathy** and provide **clear emergency guidance**. "
            "If they mention **suicidal thoughts or immediate harm**, urge them to **call 999 immediately**. "
            "Offer support options such as **Samaritans (116 123, available 24/7)** or text **SHOUT to 85258**. "
        )
    elif sentiment == "negative":
        extra_instruction = "The user is feeling low. Respond with **compassion and encouragement** using a **CBT approach**."

    previous_messages = await get_last_messages(conversation_id)

    prompt = (
        f"{SYSTEM_MESSAGE}\n\n"
        f"Previous Messages:\n{previous_messages}\n"
        f"User Message: \"{user_message}\"\n"
        f"Detected Topic: {topic}\n"
        f"Sentiment Analysis: {sentiment}\n\n"
        f"{extra_instruction}\n\n"
        f"Generate a thoughtful and structured response. Keep it concise, friendly, and natural. "
        f"Avoid repetition and unnecessary explanations. If the user acknowledges with a simple response like 'okay' or 'nice', keep your reply short and engaging."

    )

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return response.choices[0].message.content
