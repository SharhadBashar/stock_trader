import logging

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from app.v0.routes.conversations.request_model import (
    CreateConversationRequest,
    UpdateConversationRequest,
)
from app.v0.routes.conversations.response_models import ConversationResponse
from core.common.sse import TitleEvent
from core.service import stream_conversation
from db.base import get_db, get_db_session
from db.operations.conversations import conversations_ops
from db.operations.messages import messages_ops
from db.operations.users import users_ops

logger = logging.getLogger(__name__)

conversations_router = APIRouter()


def _placeholder_title(query: str) -> str:
    collapsed = ' '.join(query.split())
    if len(collapsed) <= 80:
        return collapsed
    return f'{collapsed[:80].rstrip()}...'


@conversations_router.post('', tags = ['Conversations'])
async def conversation(
    request: CreateConversationRequest,
    db: Session = Depends(get_db),
):
    query = request.query.strip()
    if not query:
        raise HTTPException(
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail = 'query is required',
        )

    user = users_ops.get(db, request.user_id)
    if not user:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = 'User not found',
        )

    created = conversations_ops.create(db, {
        'user_id': request.user_id,
        'title': _placeholder_title(query),
    })
    user_message = messages_ops.create_user_message(db, created.id, query)

    async def generate_sse_events():
        try:
            async for fragment in stream_conversation(
                query = query,
                conversation_id = created.id,
                user_id = created.user_id,
                title = created.title,
                user_message_id = user_message.id,
            ):
                if isinstance(fragment, TitleEvent):
                    with get_db_session() as title_db:
                        conversations_ops.update_title(
                            title_db,
                            created.id,
                            fragment.title,
                        )
                yield fragment.to_sse().encode()
        except Exception:
            logger.exception('Error in conversation SSE stream')
            raise

    return EventSourceResponse(generate_sse_events())


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
