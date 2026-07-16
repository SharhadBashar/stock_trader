import asyncio

from core.agents.orchestrator.agent import orchestrator_agent
from core.common.observability.pydantic_logfire.instrument_logfire import instrument_logfire, get_logfire

@instrument_logfire(project = 'trader')
async def stream(query: str):
    logfire = get_logfire()
    with logfire.span(f'{query}'):
        result = await orchestrator_agent.run(query)
        logfire.info(f'{result.output}')
        print(result.output)


if __name__ == '__main__':
    asyncio.run(stream('Get me information about Apple Inc. using the search tool'))
