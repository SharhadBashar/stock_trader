import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.v0.routes.auth.response_model import UserProfileResponse
from core.auth import get_current_user
from core.traders.liquid.auth import authenticate_liquid_sync, is_liquid_authenticated
from core.traders.robinhood.auth import authenticate_robinhood_sync, is_robinhood_authenticated
from db.models import User

logger = logging.getLogger(__name__)

auth_router = APIRouter()


@auth_router.get('/me', tags = ['Auth'], status_code = status.HTTP_200_OK, response_model = UserProfileResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


@auth_router.get('/robinhood', tags = ['Auth'], status_code = status.HTTP_200_OK)
async def robinhood_status():
    return await is_robinhood_authenticated()


@auth_router.post('/robinhood', tags = ['Auth'], status_code = status.HTTP_201_CREATED)
async def robinhood_login():
    try:
        await asyncio.to_thread(authenticate_robinhood_sync)
    except Exception:
        logger.exception('Robinhood authentication failed')
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = 'Robinhood authentication failed',
        ) from None
    return True


@auth_router.get('/liquid', tags = ['Auth'], status_code = status.HTTP_200_OK)
async def liquid_status():
    return await is_liquid_authenticated()


@auth_router.post('/liquid', tags = ['Auth'], status_code = status.HTTP_201_CREATED)
async def liquid_login():
    try:
        await asyncio.to_thread(authenticate_liquid_sync)
    except Exception:
        logger.exception('Liquid authentication failed')
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = 'Liquid authentication failed',
        ) from None
    return True
