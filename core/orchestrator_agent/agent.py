from pydantic_ai import Agent
from pydantic_ai_harness.subagents import SubAgent, SubAgents

from core.common.pydantic_ai.models import gpt_5_6_luna

from core.orchestrator_agent import (
    charts_agent,
    equity_agent,
    liquid_research_agent,
    platform_agent,
    portfolio_agent,
    profile_agent,
    research_agent,
    search_agent,
    trading_agent,
)
from core.orchestrator_agent.prompt import PROMPT

sub_agents = [
    SubAgent(profile_agent),
    SubAgent(search_agent),
    SubAgent(equity_agent),
    SubAgent(research_agent),
    SubAgent(liquid_research_agent),
    SubAgent(portfolio_agent),
    SubAgent(trading_agent),
    SubAgent(charts_agent),
    SubAgent(platform_agent),
]

orchestrator_agent = Agent(
    gpt_5_6_luna,
    name = 'orchestrator_agent',
    instructions = PROMPT,
    capabilities = [
        SubAgents(
            sub_agents
        )
    ],
    output_type = str,
)
