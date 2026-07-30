import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
LOGFIRE_TOKEN = os.getenv('LOGFIRE_TOKEN')
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')

DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB = os.getenv('DB')

# Path to the Firebase service account JSON used by firebase-admin
GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

def validate_environment():
    if not OPENAI_API_KEY:
        raise ValueError('OPENAI_API_KEY is not set')
    if not ANTHROPIC_API_KEY:
        raise ValueError('ANTHROPIC_API_KEY is not set')
    if not GEMINI_API_KEY:
        raise ValueError('GEMINI_API_KEY is not set')
    if not GROQ_API_KEY:
        raise ValueError('GROQ_API_KEY is not set')
    if not LOGFIRE_TOKEN:
        raise ValueError('LOGFIRE_TOKEN is not set')
    if not PERPLEXITY_API_KEY:
        raise ValueError('PERPLEXITY_API_KEY is not set')
    if not DB_USER:
        raise ValueError('DB_USER is not set')
    if not DB_PASSWORD:
        raise ValueError('DB_PASSWORD is not set')
    if not DB_HOST:
        raise ValueError('DB_HOST is not set')
    if not DB_PORT:
        raise ValueError('DB_PORT is not set')
    if not DB:
        raise ValueError('DB is not set')
    if not GOOGLE_APPLICATION_CREDENTIALS:
        raise ValueError('GOOGLE_APPLICATION_CREDENTIALS is not set')
