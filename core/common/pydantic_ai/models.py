from pydantic_ai.models.anthropic import AnthropicModel, AnthropicModelSettings
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings

from core.common.pydantic_ai.model_providers import openai_provider, anthropic_provider

gpt_5_6_luna = OpenAIResponsesModel(
    model_name="gpt-5.6-luna",
    provider=openai_provider,
    settings=OpenAIResponsesModelSettings(
        max_tokens=128000,
        openai_reasoning_summary="auto",
        openai_prompt_cache_retention="24h",
    ),
)

sonnet_5 = AnthropicModel(
    model_name="claude-sonnet-5",
    provider=anthropic_provider,
        settings=AnthropicModelSettings(
        max_tokens=128000,
        anthropic_cache=True,
    ),
)
fable_5 = AnthropicModel(
    model_name = 'claude-fable-5',
    provider=anthropic_provider,
        settings=AnthropicModelSettings(
        max_tokens=128000,
        anthropic_cache=True,
    ),
)
