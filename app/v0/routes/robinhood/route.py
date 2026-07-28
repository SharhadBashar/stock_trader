import logging

from fastapi import APIRouter, HTTPException

from core.robinhood.tools import robinhood_client

logger = logging.getLogger(__name__)

robinhood_router = APIRouter()


@robinhood_router.get('/login', tags = ['Robinhood'])
async def login():
    # Connecting triggers the OAuth flow (opens a browser on first use);
    # the token is persisted to the DiskStore cache by the client.
    client = robinhood_client()
    try:
        async with client:
            await client.ping()
    except Exception:
        logger.exception('Robinhood OAuth login failed')
        raise HTTPException(status_code = 502, detail = 'Robinhood login failed')

    return {'message': 'Logged in to Robinhood; token stored'}
