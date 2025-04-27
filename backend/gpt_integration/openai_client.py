import os
from dotenv import load_dotenv
import openai

# load .env and configure API key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def chat_completion(prompt: str,
                    model: str = "gpt-4",
                    temperature: float = 0.7,
                    system_message: str = "You are a helpful assistant.") -> str:
    """
    Send a chat-style prompt to OpenAI and return the assistant's reply.
    """
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system",  "content": system_message},
            {"role": "user",    "content": prompt}
        ],
        temperature=temperature,
    )
    return response.choices[0].message.content