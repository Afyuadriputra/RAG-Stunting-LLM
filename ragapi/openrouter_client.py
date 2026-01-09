from openai import OpenAI
from django.conf import settings

_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.OPENROUTER_API_KEY,
)

def chat(messages, max_tokens=1000):
    resp = _client.chat.completions.create(
        model=settings.OPENROUTER_MODEL,
        messages=messages,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content
