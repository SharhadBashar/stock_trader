from pydantic_ai import Agent, RunContext
from pydantic_ai.toolsets import AbstractToolset

from core.common.pydantic_ai.models import gpt_5_6_luna

from core.traders.robinhood.sub_agents.market_data_agent.prompt import PROMPT
from core.traders.robinhood.tools import robinhood_toolset
from core.traders.robinhood.tool_mappings import RobinhoodToolType

market_data_agent = Agent(
    gpt_5_6_luna,
    name = 'robinhood_market_data_agent',
    description = 'An agent that retrieves equity historicals, fundamentals, financials, technicals, earnings, and index data from Robinhood',
    instructions = PROMPT,
)

@market_data_agent.toolset(id = 'robinhood_market_data_tools')
def robinhood_market_data_tools(_ctx: RunContext) -> AbstractToolset:
    return robinhood_toolset(RobinhoodToolType.MARKET_DATA).defer_loading()
