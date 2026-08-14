from pydantic_ai.models.anthropic import AnthropicModel, AnthropicModelSettings
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings

from core.common.pydantic_ai.model_providers import openai_provider, anthropic_provider

gpt_5_6_luna = OpenAIResponsesModel(
    model_name = 'gpt-5.6-luna',
    provider = openai_provider,
    settings = OpenAIResponsesModelSettings(
        max_tokens = 128000,
        openai_reasoning_effort = 'none',
        openai_reasoning_summary = 'concise',
        openai_prompt_cache_retention = '24h',
    ),
)
gpt_5_6_terra = OpenAIResponsesModel(
    model_name = 'gpt-5.6-terra',
    provider = openai_provider,
    settings = OpenAIResponsesModelSettings(
        max_tokens = 128000,
        openai_reasoning_effort = 'max',
        openai_reasoning_summary = 'detailed',
        openai_prompt_cache_retention = '24h',
    ),
)

sonnet_5 = AnthropicModel(
    model_name = 'claude-sonnet-5',
    provider = anthropic_provider,
    settings = AnthropicModelSettings(
        anthropic_reasoning_effort = 'high',
        max_tokens = 128000,
        anthropic_cache = '1h',
    ),
)
fable_5 = AnthropicModel(
    model_name = 'claude-fable-5',
    provider = anthropic_provider,
    settings = AnthropicModelSettings(
        anthropic_reasoning_effort = 'xhigh',
        max_tokens = 128000,
        anthropic_cache = '1h',
    ),
)
