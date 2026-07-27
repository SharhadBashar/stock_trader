from pydantic_ai import Agent, RunContext
from pydantic_ai.toolsets import AbstractToolset

from core.common.pydantic_ai.models import gpt_5_6_luna

from core.traders.liquid.agents.platform_agent.prompt import PROMPT
from core.traders.liquid.tools import liquid_toolset
from core.traders.liquid.tool_mappings import LiquidToolType

platform_agent = Agent(
    gpt_5_6_luna,
    name = 'liquid_platform_agent',
    description = 'An agent that manages paper trading, watchlists, and platform settings on Liquid',
    instructions = PROMPT,
)

@platform_agent.toolset(id = 'liquid_platform_tools')
def liquid_platform_tools(_ctx: RunContext) -> AbstractToolset:
    return liquid_toolset(LiquidToolType.PLATFORM).defer_loading()
