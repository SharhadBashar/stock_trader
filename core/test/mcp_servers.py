import re
from pathlib import Path
from typing import Any
import asyncio
import anyio
from fastmcp.client.auth import OAuth
from fastmcp import Client
from key_value.aio.stores.disk import DiskStore
from pydantic_ai import RunContext
from pydantic_ai.mcp import CallToolFunc, MCPToolset, ToolResult

ROBINHOOD_TRADING_MCP_URL = 'https://agent.robinhood.com/mcp/trading'

# OAuth tokens live outside the repo so they can never be committed
_TOKEN_CACHE_DIR = Path.home() / '.stock_trader' / 'mcp_tokens'

# Tool names that can move real money must be confirmed in the terminal before they run.
# Robinhood's trading MCP uses review_*_order (simulation, safe) vs place_*/cancel_*_order
# (real orders); the extra verbs cover future tools like transfers or crypto.
_MONEY_MOVING_TOOL_PATTERN = re.compile(
    r'(?:^|_)(place|cancel|replace|submit|buy|sell|transfer|withdraw|deposit)(?:_|$)',
    re.IGNORECASE,
)


async def _confirm_money_moving_tools(
    ctx: RunContext[Any],
    call_tool: CallToolFunc,
    name: str,
    args: dict[str, Any],
) -> ToolResult:
    if _MONEY_MOVING_TOOL_PATTERN.search(name):
        prompt = (
            f'\n[robinhood] The agent wants to call {name!r} with:\n'
            f'  {args}\n'
            f'Approve? [y/N] '
        )
        answer = await anyio.to_thread.run_sync(input, prompt)
        if answer.strip().lower() not in ('y', 'yes'):
            return (
                'The user rejected this tool call. Do not retry it. '
                'Tell the user what you wanted to do and ask how to proceed.'
            )
    return await call_tool(name, args)


async def robinhood_trading_toolset(confirm_trades: bool = True) -> MCPToolset:
    # '''Toolset for Robinhood's hosted trading MCP server.

    # First use opens a browser for Robinhood OAuth login (PKCE + dynamic client
    # registration); tokens are cached in ~/.stock_trader/mcp_tokens so later runs
    # skip the browser until the refresh token expires.
    # '''
    # oauth = OAuth(
    #     mcp_url=ROBINHOOD_TRADING_MCP_URL,
    #     scopes='internal',
    #     client_name='stock_trader',
    #     token_storage=FileTreeStore(data_directory=_TOKEN_CACHE_DIR),
    #     callback_port=44553,
    # )
    # print(oauth)
    # toolset = MCPToolset(
    #     ROBINHOOD_TRADING_MCP_URL,
    #     id='robinhood_trading',
    #     auth=oauth,
    #     process_tool_call=_confirm_money_moving_tools if confirm_trades else None,
    # )
    # print(toolset)
    oauth = OAuth(
        mcp_url=ROBINHOOD_TRADING_MCP_URL,
        client_name = 'robinhood_trading',
        token_storage=DiskStore(directory=_TOKEN_CACHE_DIR),
        callback_port=44553,
    )
    toolset = MCPToolset(
        ROBINHOOD_TRADING_MCP_URL,
        id='robinhood_trading',
        auth=oauth,
        
    )
    tools = await toolset.list_tools()
    print(f'{len(tools)} tools:')
    for tool in tools:
        print(f'- {tool.name}')
    return toolset

    


asyncio.run(robinhood_trading_toolset())


