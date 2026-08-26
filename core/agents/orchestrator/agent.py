from pydantic_ai import Agent
from pydantic_ai_harness.subagents import SubAgent, SubAgents

from core.common.pydantic_ai.models import gpt_5_6_terra

from core.agents import liquid_agent, research_agent, robinhood_agent
from core.agents.orchestrator.prompt import PROMPT

sub_agents = [
    SubAgent(robinhood_agent),
    SubAgent(liquid_agent),
    SubAgent(research_agent),
]

orchestrator_agent = Agent(
    gpt_5_6_terra,
    name = 'orchestrator_agent',
    instructions = PROMPT,
    capabilities = [
        SubAgents(
            sub_agents
        )
    ],
    output_type = str,
)
