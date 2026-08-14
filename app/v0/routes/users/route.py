import logging

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.v0.routes.users.request_model import CreateUserRequest, UpdateUserRequest
from app.v0.routes.users.response_models import UserResponse
from db.base import get_db
from db.operations.users import users_ops

logger = logging.getLogger(__name__)

users_router = APIRouter()


@users_router.post('', tags = ['Users'], response_model = UserResponse)
async def get_or_create_user(
    request: CreateUserRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    firebase_id = request.firebase_id.strip()
    name = request.name.strip()
    email = request.email.strip().lower()
    phone = (request.phone or '').strip() or None

    if not firebase_id or not name or not email:
        raise HTTPException(
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail = 'firebase_id, name, and email are required',
        )

    existing = users_ops.get_by_firebase_id(db, firebase_id)
    if existing:
        response.status_code = status.HTTP_200_OK
        return existing

    if users_ops.get_by_email(db, email):
        raise HTTPException(
            status_code = status.HTTP_409_CONFLICT,
            detail = 'Email already registered',
        )

    try:
        user = users_ops.create(db, {
            'firebase_id': firebase_id,
            'name': name,
            'email': email,
            'phone': phone,
        })
    except IntegrityError:
        db.rollback()
        existing = users_ops.get_by_firebase_id(db, firebase_id)
        if existing:
            response.status_code = status.HTTP_200_OK
            return existing
        logger.exception('User create conflict')
        raise HTTPException(
            status_code = status.HTTP_409_CONFLICT,
            detail = 'Email already registered',
        ) from None

    response.status_code = status.HTTP_201_CREATED
    return user


@users_router.get('/{user_id}', tags = ['Users'], response_model = UserResponse)
async def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
):
    user = users_ops.get(db, user_id)
    if not user:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = 'User not found',
        )
    return user


@users_router.put('/{user_id}', tags = ['Users'], response_model = UserResponse)
async def update_user(
    user_id: UUID,
    request: UpdateUserRequest,
    db: Session = Depends(get_db),
):
    payload = request.model_dump(exclude_unset = True)
    if not payload:
        raise HTTPException(
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail = 'At least one of name or phone is required',
        )

    updates: dict = {}
    if 'name' in payload:
        name = (payload['name'] or '').strip()
        if not name:
            raise HTTPException(
                status_code = status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail = 'name cannot be empty',
            )
        updates['name'] = name
    if 'phone' in payload:
        updates['phone'] = (payload['phone'] or '').strip() or None

    user = users_ops.get(db, user_id)
    if not user:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = 'User not found',
        )

    return users_ops.update_profile(db, user_id, updates)
