from fastmcp import Client
from fastmcp.client.auth import OAuth
from key_value.aio.stores.disk import DiskStore
from pydantic_ai.mcp import MCPToolset

from core.robinhood.constants import ROBINHOOD_TRADING_MCP_URL, TOKEN_CACHE_DIR
from core.robinhood.tool_mappings import ROBINHOOD_TOOLS

def robinhood_oauth():
    return OAuth(
        mcp_url = ROBINHOOD_TRADING_MCP_URL,
        client_name = 'robinhood_trading',
        token_storage = DiskStore(directory = TOKEN_CACHE_DIR),
        callback_port = 44553,
    )

def robinhood_client():
    return Client(ROBINHOOD_TRADING_MCP_URL, auth = robinhood_oauth())

def robinhood_tools():
    return MCPToolset(ROBINHOOD_TRADING_MCP_URL, id = "robinhood_trading", auth = robinhood_oauth())

def robinhood_account_toolset() -> MCPToolset:
    account_tools = set(ROBINHOOD_TOOLS['account'])
    return robinhood_tools().filtered(
        lambda _, tool: tool.name in account_tools
    )
