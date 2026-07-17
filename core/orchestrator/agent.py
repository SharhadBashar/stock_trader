from pydantic_ai import Agent
from pydantic_ai_harness.subagents import SubAgent, SubAgents

from core.common.pydantic_ai.models import gpt_5_6_luna

from core.orchestrator import profile_agent, search_agent, equity_agent
from core.orchestrator.prompt import PROMPT

sub_agents = [
    SubAgent(profile_agent),
    SubAgent(search_agent),
    SubAgent(equity_agent),
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
    output_type=str
)
