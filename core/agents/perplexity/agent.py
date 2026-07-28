from pydantic_ai import Agent, RunContext
from pydantic_ai.toolsets import AbstractToolset

from core.common.pydantic_ai.models import fable_5
from core.agents.perplexity.prompt import PROMPT
from core.websearch.perplexity.tools import perplexity_toolset
from core.websearch.perplexity.tool_mappings import PerplexityToolType


research_agent = Agent(
    fable_5,
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
