from pydantic_ai import Agent, RunContext
from pydantic_ai.toolsets import AbstractToolset

from core.common.pydantic_ai.models import sonnet_5

from core.traders.robinhood.sub_agents.options_agent.prompt import PROMPT
from core.traders.robinhood.tools import robinhood_toolset
from core.traders.robinhood.tool_mappings import RobinhoodToolType

options_agent = Agent(
    sonnet_5,
    name = 'robinhood_options_agent',
    description = 'An agent that looks up options chains, quotes, and positions, and can place or cancel options orders on Robinhood',
    instructions = PROMPT,
)

@options_agent.toolset(id = 'robinhood_options_tools')
def robinhood_options_tools(_ctx: RunContext) -> AbstractToolset:
    return robinhood_toolset(RobinhoodToolType.OPTIONS).defer_loading()
