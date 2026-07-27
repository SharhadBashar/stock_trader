import asyncio

from fastmcp import Client
from fastmcp.client.auth import OAuth
from key_value.aio.stores.disk import DiskStore

from core.traders.robinhood.constants import (
    CALLBACK_HOST,
    CALLBACK_PORT,
    ROBINHOOD_TRADING_MCP_URL,
    TOKEN_CACHE_DIR,
)


def robinhood_oauth():
    return OAuth(
        mcp_url = ROBINHOOD_TRADING_MCP_URL,
        client_name = 'robinhood_trading',
        token_storage = DiskStore(directory = TOKEN_CACHE_DIR),
        callback_port = CALLBACK_PORT,
        callback_host = CALLBACK_HOST,
    )


def robinhood_client():
    return Client(ROBINHOOD_TRADING_MCP_URL, auth = robinhood_oauth())


async def is_robinhood_authenticated() -> bool:
    """Return True if cached Robinhood OAuth tokens exist."""
    tokens = await robinhood_oauth().token_storage_adapter.get_tokens()
    return tokens is not None and bool(tokens.access_token or tokens.refresh_token)


async def authenticate_robinhood() -> None:
    """Connect the Robinhood MCP client to trigger OAuth and cache tokens."""
    async with robinhood_client():
        pass


def authenticate_robinhood_sync() -> None:
    try:
        asyncio.run(authenticate_robinhood())
    except Exception:
        raise
    except BaseException as exc:
        raise RuntimeError(f'Robinhood authentication failed: {exc}') from exc
