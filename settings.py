import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
LOGFIRE_TOKEN = os.getenv('LOGFIRE_TOKEN')
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')

DB = os.getenv('DB')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

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
