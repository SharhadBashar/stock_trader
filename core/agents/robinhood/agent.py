from pydantic_ai import Agent
from pydantic_ai_harness.subagents import SubAgents, SubAgent

from core.traders.robinhood.sub_agents import (
    equity_agent,
    market_data_agent,
    options_agent,
    profile_agent,
    scanner_agent,
    search_agent,
    watchlist_agent,
)
from core.common.pydantic_ai.models import gpt_5_6_terra
from core.agents.robinhood.prompt import PROMPT

sub_agents = [
    SubAgent(profile_agent),
    SubAgent(search_agent),
    SubAgent(equity_agent),
    SubAgent(watchlist_agent),
    SubAgent(market_data_agent),
    SubAgent(options_agent),
    SubAgent(scanner_agent),
]

robinhood_agent = Agent(
    gpt_5_6_terra,
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