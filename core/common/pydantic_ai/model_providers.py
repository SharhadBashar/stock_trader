from openai import AsyncOpenAI
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.google import GoogleProvider

from settings import ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY, GROQ_API_KEY

openai_provider = OpenAIProvider(openai_client=AsyncOpenAI(api_key=OPENAI_API_KEY))
anthropic_provider = AnthropicProvider(api_key=ANTHROPIC_API_KEY)
gemini_provider = GoogleProvider(api_key=GEMINI_API_KEY)
