from pydantic_ai import Agent, RunContext
from pydantic_ai.toolsets import AbstractToolset

from core.common.pydantic_ai.models import sonnet_5

from core.traders.robinhood.sub_agents.equity_agent.prompt import PROMPT
from core.traders.robinhood.tools import robinhood_toolset
from core.traders.robinhood.tool_mappings import RobinhoodToolType

equity_agent = Agent(
    sonnet_5,
    name = 'robinhood_equity_agent',
    description = 'An agent that can look up stock info as well as buy and sell equities and stocks on Robinhood',
    instructions = PROMPT,
)

@equity_agent.toolset(id = 'robinhood_equity_tools')
def robinhood_equity_tools(_ctx: RunContext) -> AbstractToolset:
    return robinhood_toolset(RobinhoodToolType.EQUITIES).defer_loading()
