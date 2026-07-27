import argparse
import asyncio

from core.traders.liquid.tools import liquid_tools


async def list_tools():
    toolset = liquid_tools()
    async with toolset:
        tools = await toolset.client.list_tools()
    print(f'{len(tools)} tools available on the Liquid Co-Invest MCP:')
    for tool in tools:
        summary = (tool.description or '').strip().splitlines()[0] if tool.description else ''
        print(f'- {tool.name}: {summary}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Liquid Co-Invest MCP connection smoke test')
    parser.add_argument(
        '--list-tools',
        action = 'store_true',
        help = 'authenticate and list available Liquid Co-Invest tools',
    )
    args = parser.parse_args()

    if args.list_tools:
        asyncio.run(list_tools())
    else:
        parser.print_help()
