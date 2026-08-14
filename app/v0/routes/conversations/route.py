from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.v0.routes.conversations.request_model import (
    ConversationResponse,
    CreateConversationRequest,
    UpdateConversationRequest,
)
from db.base import get_db
from db.operations.conversations import conversations_ops
from db.operations.users import users_ops

conversations_router = APIRouter()


@conversations_router.get('', tags = ['Conversations'], response_model = list[ConversationResponse])
async def list_conversations(
    user_id: UUID | None = None,
    include_archived: bool = False,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return conversations_ops.get_by_user_id(
        db,
        user_id = user_id,
        include_archived = include_archived,
        skip = skip,
        limit = limit,
    )


@conversations_router.get(
    '/{conversation_id}',
    tags = ['Conversations'],
    response_model = ConversationResponse,
)
async def get_conversation(
    conversation_id: UUID,
    db: Session = Depends(get_db),
):
    conversation = conversations_ops.get(db, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = 'Conversation not found',
        )
    return conversation


@conversations_router.post(
    '',
    tags = ['Conversations'],
    response_model = ConversationResponse,
    status_code = status.HTTP_201_CREATED,
)
async def create_conversation(
    request: CreateConversationRequest,
    db: Session = Depends(get_db),
):
    title = request.title.strip()
    if not title:
        raise HTTPException(
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail = 'title is required',
        )

    if not users_ops.get(db, request.user_id):
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = 'User not found',
        )

    return conversations_ops.create(db, {
        'user_id': request.user_id,
        'title': title,
    })


@conversations_router.patch(
    '/{conversation_id}',
    tags = ['Conversations'],
    response_model = ConversationResponse,
)
async def update_conversation(
    conversation_id: UUID,
    request: UpdateConversationRequest,
    db: Session = Depends(get_db),
):
    title = request.title.strip()
    if not title:
        raise HTTPException(
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail = 'title is required',
        )

    conversation = conversations_ops.update_title(db, conversation_id, title)
    if not conversation:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = 'Conversation not found',
        )
    return conversation


@conversations_router.post(
    '/{conversation_id}/archive',
    tags = ['Conversations'],
    response_model = ConversationResponse,
)
async def archive_conversation(
    conversation_id: UUID,
    db: Session = Depends(get_db),
):
    conversation = conversations_ops.archive(db, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = 'Conversation not found',
        )
    return conversation
