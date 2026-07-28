from pydantic_ai import Agent
from pydantic_ai_harness.subagents import SubAgents, SubAgent

from core.traders.robinhood.sub_agents import profile_agent, search_agent, equity_agent
from core.common.pydantic_ai.models import gpt_5_6_luna
from core.agents.robinhood.prompt import PROMPT

sub_agents = [
    SubAgent(profile_agent),
    SubAgent(search_agent),
    SubAgent(equity_agent),
]

robinhood_agent = Agent(
    gpt_5_6_luna,
    name = 'robinhood_agent',
    description = 'An agent that can look up stock info as well as buy and sell equities and stocks on Robinhood',
    instructions = PROMPT,
    capabilities = [
        SubAgents(
            sub_agents
        )
    ],
    output_type = str,
)