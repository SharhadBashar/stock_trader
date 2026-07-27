from pydantic_ai import Agent, RunContext
from pydantic_ai.toolsets import AbstractToolset

from core.common.pydantic_ai.models import gpt_5_6_luna

from core.traders.liquid.agents.charts_agent.prompt import PROMPT
from core.traders.liquid.tools import liquid_toolset
from core.traders.liquid.tool_mappings import LiquidToolType

charts_agent = Agent(
    gpt_5_6_luna,
    name = 'liquid_charts_agent',
    description = 'An agent that shows charts, order books, and market overviews on Liquid',
    instructions = PROMPT,
)

@charts_agent.toolset(id = 'liquid_charts_tools')
def liquid_charts_tools(_ctx: RunContext) -> AbstractToolset:
    return liquid_toolset(LiquidToolType.CHARTS).defer_loading()
