from pydantic_ai import Agent
from pydantic_ai_harness.subagents import SubAgent, SubAgents

from core.agents import profile_agent
from core.common.pydantic_ai.models import gpt_5_6_luna
from core.agents.orchestrator.prompt import PROMPT

orchestrator_agent = Agent(
    gpt_5_6_luna,
    name = 'orchestrator_agent',
    instructions = PROMPT,
    capabilities = [
        SubAgents(
            agents = [
                SubAgent(profile_agent),
            ]
        )
    ]
)
