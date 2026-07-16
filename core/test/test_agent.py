
from pydantic_ai import Agent
from pydantic_ai_harness.subagents import SubAgent, SubAgents
from pydantic_ai.capabilities import Instrumentation
from pydantic_ai.models.instrumented import InstrumentationSettings

from core.common.observability.pydantic_logfire.instrument_logfire import instrument_logfire, get_logfire
from core.common.pydantic_ai.models import gpt_5_6_luna, sonnet_5, fable_5

researcher = Agent(
    fable_5,
    name='researcher_agent',
    description='Researches a topic and reports findings',
    instructions='You are a researcher. You are tasked with researching a topic and reporting your findings.',
    # capabilities=[Instrumentation(InstrumentationSettings())],
)
writer = Agent(
    sonnet_5,
    name='writer_agent',
    description='Turns notes into polished prose',
    instructions='You are a writer. You are tasked with turning notes into polished prose.',
    # capabilities=[Instrumentation(InstrumentationSettings())],
)

subagents = SubAgents(
    agents = [
        SubAgent(researcher, max_calls=1),
        SubAgent(writer),
    ]
)

orchestrator = Agent(
    gpt_5_6_luna,
    capabilities=[subagents],
    name='orchestrator_agent',
    description='Orchestrates the research and writing process',
    instructions='You are an orchestrator. You are tasked with orchestrating the research and writing process.',

)


@instrument_logfire(project = 'research')
def research(query: str):
    logfire = get_logfire()
    with logfire.span(f'Researching: {query}') as span:
        
        result = orchestrator.run_sync(query)
        span.set_attribute('total_tokens_i_used', result.usage.total_tokens)
        logfire.info(f'Research result: {result.output}')


if __name__ == '__main__':
    research('Research the history of TLS and write a one-paragraph summary.')
