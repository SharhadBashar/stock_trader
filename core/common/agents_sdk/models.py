import asyncio


from agents import Agent, OpenAIResponsesModel, Runner
from openai import AsyncOpenAI

from settings import OPENAI_API_KEY


agent = Agent(
    name='History Tutor',
    instructions='You answer history questions clearly and concisely.',
    model=OpenAIResponsesModel(
        model='gpt-4o-mini',
        openai_client=AsyncOpenAI(api_key=OPENAI_API_KEY),
    )
)

async def main():
    result = await Runner.run(agent, 'When did the Roman Empire fall?')
    print(result.final_output)

if __name__ == '__main__':
    asyncio.run(main())