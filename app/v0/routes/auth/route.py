import asyncio
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from core.traders.liquid.auth import authenticate_liquid_sync, is_liquid_authenticated
from core.traders.robinhood.auth import authenticate_robinhood_sync, is_robinhood_authenticated
from db import get_db
from db.user_operations import UserDBOperations

logger = logging.getLogger(__name__)

auth_router = APIRouter()

user_ops = UserDBOperations()


class SignupRequest(BaseModel):
    firebase_uuid: str
    email: str | None = None
    phone: str | None = None


class SigninRequest(BaseModel):
    firebase_uuid: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes = True)

    id: uuid.UUID
    firebase_uuid: str
    phone: str | None
    email: str | None
    created_at: datetime
    updated_at: datetime
    last_login: datetime | None
    archived_at: datetime | None


@auth_router.post('/signup', tags = ['Auth'], status_code = status.HTTP_201_CREATED, response_model = UserResponse)
async def signup(request: SignupRequest, db: Session = Depends(get_db)):
    user = user_ops.get_by_firebase_uuid(db, request.firebase_uuid)
    if user is None:
        return user_ops.create(db, {
            'firebase_uuid': request.firebase_uuid,
            'email': request.email,
            'phone': request.phone,
            'last_login': datetime.now(timezone.utc),
        })
    return user_ops.touch_last_login(db, user)


@auth_router.post('/signin', tags = ['Auth'], status_code = status.HTTP_200_OK, response_model = UserResponse)
async def signin(request: SigninRequest, db: Session = Depends(get_db)):
    user = user_ops.get_by_firebase_uuid(db, request.firebase_uuid)
    if user is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = 'User not found',
        )
    return user_ops.touch_last_login(db, user)


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
