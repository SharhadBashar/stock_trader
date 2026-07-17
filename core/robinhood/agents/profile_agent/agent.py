from pydantic_ai import Agent, RunContext
from pydantic_ai.toolsets import AbstractToolset

from core.common.pydantic_ai.models import gpt_5_6_luna

from core.robinhood.agents.profile_agent.prompt import PROMPT
from core.robinhood.tools import robinhood_toolset
from core.robinhood.tool_mappings import RobinhoodToolType

profile_agent = Agent(
    gpt_5_6_luna,
    name = 'profile_agent',
    description = 'An agent that returns your profile information from Robinhood',
    instructions = PROMPT,
)

@profile_agent.toolset(id = 'robinhood_account_tools')
def robinhood_account_tools(_ctx: RunContext) -> AbstractToolset:
    return robinhood_toolset(RobinhoodToolType.ACCOUNT).defer_loading()
