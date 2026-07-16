import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LOGFIRE_TOKEN = os.getenv("LOGFIRE_TOKEN")

def validate_environment():
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set")
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY is not set")
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY is not set")
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set")
    if not LOGFIRE_TOKEN:
        raise ValueError("LOGFIRE_TOKEN is not set")
