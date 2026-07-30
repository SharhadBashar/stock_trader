"""
Test bootstrap.

settings.py / db/base.py read the environment at import time (and app/main.py
calls validate_environment()), so dummy values must be in the environment
before anything under app/, db/ or core/auth/ is imported. No connection to
a real database or external service is ever opened in these tests.
"""

import os


os.environ.setdefault('OPENAI_API_KEY', 'test')
os.environ.setdefault('ANTHROPIC_API_KEY', 'test')
os.environ.setdefault('GEMINI_API_KEY', 'test')
os.environ.setdefault('GROQ_API_KEY', 'test')
os.environ.setdefault('LOGFIRE_TOKEN', 'test')
os.environ.setdefault('PERPLEXITY_API_KEY', 'test')

os.environ.setdefault('DB_USER', 'test')
os.environ.setdefault('DB_PASSWORD', 'test')
os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_PORT', '5432')
os.environ.setdefault('DB', 'test')
os.environ.setdefault('GOOGLE_APPLICATION_CREDENTIALS', '/tmp/fake-firebase-service-account.json')
