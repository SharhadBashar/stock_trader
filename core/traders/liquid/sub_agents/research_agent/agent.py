from pydantic_ai import Agent, RunContext
from pydantic_ai.toolsets import AbstractToolset

from core.common.pydantic_ai.models import fable_5

from core.traders.liquid.sub_agents.research_agent.prompt import PROMPT
from core.traders.liquid.tools import liquid_toolset
from core.traders.liquid.tool_mappings import LiquidToolType

research_agent = Agent(
    fable_5,
    name = 'liquid_research_agent',
    description = 'An agent that researches markets, news, and positioning on Liquid',
    instructions = PROMPT,
)

@research_agent.toolset(id = 'liquid_research_tools')
def liquid_research_tools(_ctx: RunContext) -> AbstractToolset:
    return liquid_toolset(LiquidToolType.RESEARCH).defer_loading()
