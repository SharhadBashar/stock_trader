from pydantic_ai import Agent, RunContext
from pydantic_ai.toolsets import AbstractToolset

from core.common.pydantic_ai.models import gpt_5_6_luna

from core.traders.robinhood.sub_agents.watchlist_agent.prompt import PROMPT
from core.traders.robinhood.tools import robinhood_toolset
from core.traders.robinhood.tool_mappings import RobinhoodToolType

watchlist_agent = Agent(
    gpt_5_6_luna,
    name = 'robinhood_watchlist_agent',
    description = 'An agent that manages Robinhood watchlists, including custom lists, popular lists, and options watchlists',
    instructions = PROMPT,
)

@watchlist_agent.toolset(id = 'robinhood_watchlist_tools')
def robinhood_watchlist_tools(_ctx: RunContext) -> AbstractToolset:
    return robinhood_toolset(RobinhoodToolType.WATCHLIST).defer_loading()
