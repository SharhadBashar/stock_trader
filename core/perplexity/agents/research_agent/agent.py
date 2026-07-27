from pydantic_ai import Agent, RunContext
from pydantic_ai.toolsets import AbstractToolset

from core.common.pydantic_ai.models import gpt_5_6_luna
from core.perplexity.agents.research_agent.prompt import PROMPT
from core.perplexity.tools import perplexity_toolset
from core.perplexity.tool_mappings import PerplexityToolType


research_agent = Agent(
    gpt_5_6_luna,
    name = 'perplexity_research_agent',
    description = (
        'An agent that researches markets, companies, news, and trends '
        'using Perplexity search, ask, deep research, and reasoning tools'
    ),
    instructions = PROMPT,
)


@research_agent.toolset(id = 'perplexity_tools')
def perplexity_research_tools(_ctx: RunContext) -> AbstractToolset:
    return perplexity_toolset(PerplexityToolType.ALL).defer_loading()
