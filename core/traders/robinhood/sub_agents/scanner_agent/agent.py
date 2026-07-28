from pydantic_ai import Agent, RunContext
from pydantic_ai.toolsets import AbstractToolset

from core.common.pydantic_ai.models import gpt_5_6_luna

from core.traders.robinhood.sub_agents.scanner_agent.prompt import PROMPT
from core.traders.robinhood.tools import robinhood_toolset
from core.traders.robinhood.tool_mappings import RobinhoodToolType

scanner_agent = Agent(
    gpt_5_6_luna,
    name = 'robinhood_scanner_agent',
    description = 'An agent that creates, updates, and runs Robinhood market scanners',
    instructions = PROMPT,
)

@scanner_agent.toolset(id = 'robinhood_scanner_tools')
def robinhood_scanner_tools(_ctx: RunContext) -> AbstractToolset:
    return robinhood_toolset(RobinhoodToolType.SCANNER).defer_loading()
