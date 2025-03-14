import openai
import os
from openai import OpenAI
from dotenv import load_dotenv
from django.conf import settings
# Load environment variables
load_dotenv()
openai_api_key = "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"
client = OpenAI(api_key=openai_api_key)


def analyze_sentiment(message):
    """Uses AI to classify sentiment: Positive, Neutral, Negative, or Critical."""
    prompt = f"Analyze the sentiment of this message: '{message}'. Output only one word: Positive, Neutral, Negative, or Critical."

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return response.choices[0].message.content

def detect_topic(message):
    """Classifies topics: Self-Harm, Abuse, Grooming, Bullying, Academic Stress, or Other."""
    prompt = f"Categorise the message '{message}' into one of: Self-Harm, Abuse, Grooming, Bullying, Academic Stress, Other. Output only one word."

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return response.choices[0].message.content


