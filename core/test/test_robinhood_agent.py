import argparse
import asyncio

from pydantic_ai import Agent

from core.common.observability.pydantic_logfire.instrument_logfire import instrument_logfire, get_logfire
from core.common.pydantic_ai.models import fable_5
from core.test.mcp_servers import robinhood_trading_toolset

robinhood_toolset = robinhood_trading_toolset()

trader = Agent(
    fable_5,
    name='robinhood_trader_agent',
    description='Answers questions about your Robinhood portfolio and the market using Robinhood trading tools',
    instructions=(
        'You are a stock trading assistant connected to the user\'s real Robinhood agentic account. '
        'Use the Robinhood tools to look up portfolio positions, quotes, and market data. '
        'Never place, modify, or cancel an order unless the user explicitly asked for that exact trade. '
        'Before placing any order, always call the matching review_*_order tool first and report its warnings. '
        'Money-moving tools require terminal confirmation from the user before they execute.'
    ),
    toolsets=[robinhood_toolset],
)


async def list_tools():
    async with robinhood_toolset:
        tools = await robinhood_toolset.client.list_tools()
    print(f'{len(tools)} tools available on the Robinhood trading MCP:')
    for tool in tools:
        summary = (tool.description or '').strip().splitlines()[0] if tool.description else ''
        print(f'- {tool.name}: {summary}')


@instrument_logfire(project='robinhood')
def trade(query: str):
    logfire = get_logfire()
    with logfire.span(f'Robinhood agent: {query}') as span:
        result = trader.run_sync(query)
        span.set_attribute('total_tokens_i_used', result.usage.total_tokens)
        logfire.info(f'Robinhood agent result: {result.output}')
        print(result.output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Robinhood trading agent')
    parser.add_argument('--list-tools', action='store_true', help='authenticate and list available Robinhood tools')
    parser.add_argument(
        'query',
        nargs='?',
        default='Give me a summary of my portfolio: each position, its current price, and how it moved today.',
    )
    args = parser.parse_args()

    if args.list_tools:
        asyncio.run(list_tools())
    else:
        trade(args.query)
