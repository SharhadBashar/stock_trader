import argparse
import asyncio
import sys

from core.perplexity.tool_mappings import PERPLEXITY_TOOLS, PerplexityToolType
from core.perplexity.tools import perplexity_tools

EXPECTED_TOOLS = set(PERPLEXITY_TOOLS[PerplexityToolType.ALL])


async def list_tools() -> list[str]:
    toolset = perplexity_tools()
    async with toolset:
        tools = await toolset.list_tools()
    names = [tool.name for tool in tools]
    print(f'{len(names)} tools available on the Perplexity MCP:')
    for tool in tools:
        summary = (tool.description or '').strip().splitlines()[0] if tool.description else ''
        print(f'- {tool.name}: {summary}')
    return names


async def ask(query: str) -> None:
    toolset = perplexity_tools()
    result = await toolset.direct_call_tool(
        'perplexity_ask',
        {'messages': [{'role': 'user', 'content': query}]},
    )
    print(result)


async def main() -> None:
    parser = argparse.ArgumentParser(description = 'Perplexity MCP smoke test')
    parser.add_argument('--list-tools', action = 'store_true', help = 'list available Perplexity MCP tools')
    parser.add_argument(
        '--ask',
        nargs = '?',
        const = 'What is the S&P 500?',
        help = 'optionally call perplexity_ask with a query',
    )
    args = parser.parse_args()

    if not args.list_tools and args.ask is None:
        args.list_tools = True

    if args.list_tools:
        names = await list_tools()
        missing = EXPECTED_TOOLS - set(names)
        if missing:
            print(f'Missing expected tools: {sorted(missing)}', file = sys.stderr)
            raise SystemExit(1)
        print('All expected Perplexity tools are present.')

    if args.ask is not None:
        await ask(args.ask)


if __name__ == '__main__':
    asyncio.run(main())
