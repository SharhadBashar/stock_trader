from enum import Enum


class InstrumentType(Enum):
    PYDANTIC_AI = 'pydantic_ai'
    OPENAI = 'openai'
    ANTHROPIC = 'anthropic'
    GOOGLE = 'google'
    GROQ = 'groq'
