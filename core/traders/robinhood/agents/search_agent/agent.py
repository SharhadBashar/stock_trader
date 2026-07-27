from pydantic_ai import Agent, RunContext
from pydantic_ai.toolsets import AbstractToolset

from core.common.pydantic_ai.models import gpt_5_6_luna

from core.traders.robinhood.agents.search_agent.prompt import PROMPT
from core.traders.robinhood.tools import robinhood_toolset
from core.traders.robinhood.tool_mappings import RobinhoodToolType

search_agent = Agent(
    gpt_5_6_luna,
    name = 'robinhood_search_agent',
    description = 'An agent that searches for information about a company on Robinhood',
    instructions = PROMPT,
)

@search_agent.toolset(id = 'robinhood_search_tools')
def robinhood_search_tools(_ctx: RunContext) -> AbstractToolset:
    return robinhood_toolset(RobinhoodToolType.SEARCH).defer_loading()
