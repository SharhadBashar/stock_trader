import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.v0.routes.users.request_model import CreateUserRequest, UserResponse
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
