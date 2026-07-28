from pydantic_ai import Agent, RunContext
from pydantic_ai.toolsets import AbstractToolset

from core.common.pydantic_ai.models import gpt_5_6_luna

from core.traders.liquid.sub_agents.portfolio_agent.prompt import PROMPT
from core.traders.liquid.tools import liquid_toolset
from core.traders.liquid.tool_mappings import LiquidToolType

portfolio_agent = Agent(
    gpt_5_6_luna,
    name = 'liquid_portfolio_agent',
    description = 'An agent that returns portfolio, positions, and transaction info from Liquid',
    instructions = PROMPT,
)

@portfolio_agent.toolset(id = 'liquid_portfolio_tools')
def liquid_portfolio_tools(_ctx: RunContext) -> AbstractToolset:
    return liquid_toolset(LiquidToolType.PORTFOLIO).defer_loading()
