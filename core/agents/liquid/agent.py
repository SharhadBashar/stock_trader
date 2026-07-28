from pydantic_ai import Agent
from pydantic_ai_harness.subagents import SubAgent, SubAgents

from core.common.pydantic_ai.models import gpt_5_6_terra
from core.agents.liquid.prompt import PROMPT
from core.traders.liquid.sub_agents import (
    charts_agent,
    platform_agent,
    portfolio_agent,
    research_agent,
    trading_agent,
)

sub_agents = [
    SubAgent(research_agent),
    SubAgent(portfolio_agent),
    SubAgent(trading_agent),
    SubAgent(charts_agent),
    SubAgent(platform_agent),
]

liquid_agent = Agent(
    gpt_5_6_terra,
    name = 'liquid_agent',
    description = 'An agent that researches markets, manages portfolio and trades, and shows charts on Liquid Co-Invest',
    instructions = PROMPT,
    capabilities = [
        SubAgents(
            sub_agents
        )
    ],
    output_type = str,
)
