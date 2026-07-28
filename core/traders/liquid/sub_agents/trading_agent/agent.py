from pydantic_ai import Agent, RunContext
from pydantic_ai.toolsets import AbstractToolset

from core.common.pydantic_ai.models import sonnet_5

from core.traders.liquid.sub_agents.trading_agent.prompt import PROMPT
from core.traders.liquid.tools import liquid_toolset
from core.traders.liquid.tool_mappings import LiquidToolType

trading_agent = Agent(
    sonnet_5,
    name = 'liquid_trading_agent',
    description = 'An agent that can suggest and manage trades and positions on Liquid',
    instructions = PROMPT,
)

@trading_agent.toolset(id = 'liquid_trading_tools')
def liquid_trading_tools(_ctx: RunContext) -> AbstractToolset:
    return liquid_toolset(LiquidToolType.TRADING).defer_loading()
