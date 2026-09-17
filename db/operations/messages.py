import json
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from db.base_operations import BaseDBOperations
from db.models.conversations import Conversation
from db.models.messages import Message


def jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (bytes, bytearray)):
        return value.decode('utf-8', errors = 'replace')
    try:
        return json.loads(json.dumps(value, default = str))
    except (TypeError, ValueError):
        return str(value)


def parse_tool_args(args: Any) -> Any:
    if isinstance(args, str):
        try:
            return json.loads(args)
        except json.JSONDecodeError:
            return args
    return jsonable(args)


def _role_for(msg_type: str, user_message_id: UUID | None) -> str:
    if user_message_id is None:
        return 'user'
    if msg_type == 'tool_result':
        return 'tool'
    return 'assistant'


class MessagesDBOperations(BaseDBOperations[Message]):
    def __init__(self):
        super().__init__(Message)

    def _next_sequence(self, db: Session, user_message_id: UUID) -> int:
        max_sequence = (
            db.query(func.max(self.model.sequence))
            .filter(self.model.user_message_id == user_message_id)
            .scalar()
        )
        return 0 if max_sequence is None else max_sequence + 1

    def _touch_conversation(self, db: Session, conversation_id: UUID) -> None:
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation:
            conversation.updated_at = datetime.now()

    def create_message(
        self,
        db: Session,
        conversation_id: UUID,
        msg_type: str,
        content: dict | None,
        *,
        user_message_id: UUID | None = None,
        role: str | None = None,
        status: str | None = None,
        call_id: str | None = None,
        tool_name: str | None = None,
        delegate_agent_name: str | None = None,
        agent_name: str | None = None,
        model: str | None = None,
    ) -> Message:
        row = self.create(db, {
            'conversation_id': conversation_id,
            'user_message_id': user_message_id,
            'role': role or _role_for(msg_type, user_message_id),
            'msg_type': msg_type,
            'sequence': 0 if user_message_id is None else self._next_sequence(db, user_message_id),
            'sibling_index': 0,
            'call_id': call_id,
            'agent_name': agent_name,
            'model': model,
            'tool_name': tool_name,
            'delegate_agent_name': delegate_agent_name,
            'content': jsonable(content),
            'status': status,
            'visibility': 'all',
        })
        self._touch_conversation(db, conversation_id)
        db.commit()
        db.refresh(row)
        return row


messages_ops = MessagesDBOperations()
