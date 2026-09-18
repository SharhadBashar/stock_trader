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
    return json.loads(json.dumps(value, default = str))


def parse_tool_args(args: Any) -> Any:
    if isinstance(args, str):
        try:
            return json.loads(args)
        except json.JSONDecodeError:
            return args
    return jsonable(args)


class MessagesDBOperations(BaseDBOperations[Message]):
    def __init__(self):
        super().__init__(Message)

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
    ) -> Message:
        if role is None:
            if user_message_id is None:
                role = 'user'
            elif msg_type == 'tool_result':
                role = 'tool'
            else:
                role = 'assistant'

        sequence = 0
        if user_message_id is not None:
            max_sequence = (
                db.query(func.max(self.model.sequence))
                .filter(self.model.user_message_id == user_message_id)
                .scalar()
            )
            sequence = 0 if max_sequence is None else max_sequence + 1

        row = self.create(db, {
            'conversation_id': conversation_id,
            'user_message_id': user_message_id,
            'role': role,
            'msg_type': msg_type,
            'sequence': sequence,
            'sibling_index': 0,
            'call_id': call_id,
            'agent_name': agent_name,
            'tool_name': tool_name,
            'delegate_agent_name': delegate_agent_name,
            'content': jsonable(content),
            'status': status,
            'visibility': 'all',
        })
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation:
            conversation.updated_at = datetime.now()
            db.commit()
            db.refresh(row)
        return row


messages_ops = MessagesDBOperations()
