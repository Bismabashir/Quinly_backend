from .system_message import SYSTEM_MESSAGE
import os
from dotenv import load_dotenv
from openai import OpenAI
from django.conf import settings
from .models import Message # added function from models file

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)


# def generate_ai_response(user_message, topic, sentiment, is_premium):
#     # """Generates chatbot responses dynamically with tiered AI models."""

#     # Choose GPT version based on user tier
#     model = "gpt-4o" if is_premium else "gpt-3.5-turbo"

#     # Adjust system message dynamically based on topic & sentiment
#     extra_instruction = ""

#     # if sentiment == "critical":
#     #     extra_instruction = "This user is in a critical emotional state. Respond with high empathy and provide immediate help resources."
#     # elif sentiment == "negative":
#     #     extra_instruction = "The user is feeling low. Use a CBT approach to guide them positively."
#     if sentiment == "critical":
#         extra_instruction = (
#             "This user is in a **critical emotional state**. Use **high empathy** and provide **clear emergency guidance**. "
#             "If they mention **suicidal thoughts or immediate harm**, urge them to **call 999 immediately**. "
#             "Offer support options such as **Samaritans (116 123, available 24/7)** or text **SHOUT to 85258**. "
#             "Avoid giving generic reassurance; instead, validate their feelings and ask a gentle follow-up question like: "
#             "'Would you like me to suggest coping strategies or someone to talk to?'"
#         )
#     elif sentiment == "negative":
#         extra_instruction = (
#             "The user is feeling low. Respond with **compassion and encouragement**, following a **CBT approach**. "
#             "Gently ask about their thoughts, feelings, and actions separately to help guide them toward a solution."
#             "Do not mention the emergency triggers in this case i.e;call 999 immediately.  "
#         )

#     # prompt = f"{SYSTEM_MESSAGE}\n{extra_instruction}\nUser message: {user_message}\nDetected Topic: {topic}\nGenerate an empathetic response."
#     prompt = (
#         f"{SYSTEM_MESSAGE}\n\n"
#         f"User Message: \"{user_message}\"\n"
#         f"Detected Topic: {topic}\n"
#         f"Sentiment Analysis: {sentiment}\n\n"
#         f"{extra_instruction}\n\n"
#         f"Generate a thoughtful and structured response."
#     )

#     response = client.chat.completions.create(
#         model=model,
#         messages=[{"role": "user", "content": prompt}],
#         temperature=0.2
#     )

#     return response.choices[0].message.content


async def get_last_messages(conversation_id, limit=5):
    """Retrieve last few messages from a conversation for better context."""
    messages = await Message.objects.filter(conversation_id=conversation_id).order_by("-created_at")[:limit]
    return "\n".join([f"User: {msg.user_message}\nBot: {msg.bot_response}" for msg in messages if msg.user_message])

async def generate_ai_response(user_message, topic, sentiment, is_premium, conversation_id):
    """Generates chatbot responses dynamically with tiered AI models and conversation context."""
    
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

    # Fetch last few messages for context
    previous_messages = await get_last_messages(conversation_id)

    prompt = (
        f"{SYSTEM_MESSAGE}\n\n"
        f"Previous Messages:\n{previous_messages}\n"
        f"User Message: \"{user_message}\"\n"
        f"Detected Topic: {topic}\n"
        f"Sentiment Analysis: {sentiment}\n\n"
        f"{extra_instruction}\n\n"
        f"Generate a thoughtful and structured response."
    )

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return response.choices[0].message.content
