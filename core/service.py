import asyncio
import json

from core.orchestrator.agent import orchestrator_agent
from core.common.observability.pydantic_logfire.instrument_logfire import instrument_logfire, get_logfire

@instrument_logfire(project = 'trader')
async def stream(query: str):
    logfire = get_logfire()
    with logfire.span('{query}', query = query):
        result = await orchestrator_agent.run(query)
        model = orchestrator_agent.model
        logfire.info(
            'Final Output',
            **{
                'gen_ai.input.messages': [
                    {'role': 'user', 'parts': [{'type': 'text', 'content': query}]},
                ],
                'gen_ai.output.messages': [
                    {'role': 'assistant', 'parts': [{'type': 'text', 'content': result.output}]},
                ],
            },
        )
        
if __name__ == '__main__':
    asyncio.run(stream('Get me information about Apple, as well as their current stock price'))
