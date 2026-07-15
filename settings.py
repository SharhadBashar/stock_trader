import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def validate_environment():
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set")
