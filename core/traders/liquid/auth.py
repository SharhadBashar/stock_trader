import asyncio

from fastmcp import Client
from fastmcp.client.auth import OAuth
from key_value.aio.stores.disk import DiskStore

from core.traders.liquid.constants import (
    CALLBACK_HOST,
    CALLBACK_PORT,
    LIQUID_COINVEST_MCP_URL,
    TOKEN_CACHE_DIR,
)


def liquid_oauth():
    return OAuth(
        mcp_url = LIQUID_COINVEST_MCP_URL,
        client_name = 'liquid_coinvest',
        token_storage = DiskStore(directory = TOKEN_CACHE_DIR),
        callback_port = CALLBACK_PORT,
        callback_host = CALLBACK_HOST,
    )


def liquid_client():
    return Client(LIQUID_COINVEST_MCP_URL, auth = liquid_oauth())


async def is_liquid_authenticated() -> bool:
    """Return True if cached Liquid OAuth tokens exist."""
    tokens = await liquid_oauth().token_storage_adapter.get_tokens()
    return tokens is not None and bool(tokens.access_token or tokens.refresh_token)


async def authenticate_liquid() -> None:
    """Connect the Liquid MCP client to trigger OAuth and cache tokens."""
    async with liquid_client():
        pass


def authenticate_liquid_sync() -> None:
    try:
        asyncio.run(authenticate_liquid())
    except Exception:
        raise
    except BaseException as exc:
        raise RuntimeError(f'Liquid authentication failed: {exc}') from exc
