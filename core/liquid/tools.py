import asyncio

from fastmcp import Client
from fastmcp.client.auth import OAuth
from key_value.aio.stores.disk import DiskStore
from pydantic_ai.mcp import MCPToolset

from core.liquid.constants import CALLBACK_PORT, LIQUID_COINVEST_MCP_URL, TOKEN_CACHE_DIR


def liquid_oauth():
    return OAuth(
        mcp_url = LIQUID_COINVEST_MCP_URL,
        client_name = 'liquid_coinvest',
        token_storage = DiskStore(directory = TOKEN_CACHE_DIR),
        callback_port = CALLBACK_PORT,
    )


def liquid_client():
    return Client(LIQUID_COINVEST_MCP_URL, auth = liquid_oauth())


def liquid_tools():
    return MCPToolset(LIQUID_COINVEST_MCP_URL, id = 'liquid_coinvest', auth = liquid_oauth())


async def _list_tools():
    async with liquid_client() as client:
        tools = await client.list_tools()
    print(f'{len(tools)} tools available on the Liquid Co-Invest MCP:')
    for tool in tools:
        summary = (tool.description or '').strip().splitlines()[0] if tool.description else ''
        print(f'- {tool.name}: {summary}')
        print('\n')


if __name__ == '__main__':
    asyncio.run(_list_tools())
