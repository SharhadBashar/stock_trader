import json
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

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

    def _turn_rows(self, db: Session, user_message_id: UUID) -> list[Message]:
        return (
            db.query(self.model)
            .filter(
                or_(
                    self.model.id == user_message_id,
                    self.model.user_message_id == user_message_id,
                )
            )
            .order_by(self.model.sequence.asc(), self.model.sibling_index.asc())
            .all()
        )

    def _touch_conversation(self, db: Session, conversation_id: UUID) -> None:
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation:
            conversation.updated_at = datetime.now()

    def list_by_conversation(self, db: Session, conversation_id: UUID) -> list[Message]:
        return (
            db.query(self.model)
            .filter(
                self.model.conversation_id == conversation_id,
                self.model.archived_at.is_(None),
            )
            .order_by(self.model.created_at.asc(), self.model.sequence.asc())
            .all()
        )

    def create_user_message(self, db: Session, conversation_id: UUID, query: str) -> Message:
        row = self.create(db, {
            'conversation_id': conversation_id,
            'user_message_id': None,
            'parent_message_id': None,
            'role': 'user',
            'msg_type': 'text',
            'sequence': 0,
            'sibling_index': 0,
            'content': {'text': query},
            'status': 'pending',
            'visibility': 'all',
        })
        self._touch_conversation(db, conversation_id)
        db.commit()
        db.refresh(row)
        return row

    def append_event(
        self,
        db: Session,
        *,
        conversation_id: UUID,
        user_message_id: UUID,
        role: str,
        msg_type: str,
        content: dict | None = None,
        status: str | None = None,
        call_id: str | None = None,
        agent_name: str | None = None,
        parent_agent_name: str | None = None,
        model: str | None = None,
        tool_name: str | None = None,
        delegate_agent_name: str | None = None,
        parent_message_id: UUID | None = None,
        provider_message_id: str | None = None,
        log: dict | None = None,
        sibling_index: int = 0,
        visibility: str = 'all',
    ) -> Message:
        row = self.create(db, {
            'conversation_id': conversation_id,
            'user_message_id': user_message_id,
            'parent_message_id': parent_message_id,
            'role': role,
            'msg_type': msg_type,
            'sequence': self._next_sequence(db, user_message_id),
            'sibling_index': sibling_index,
            'call_id': call_id,
            'agent_name': agent_name,
            'parent_agent_name': parent_agent_name,
            'model': model,
            'tool_name': tool_name,
            'delegate_agent_name': delegate_agent_name,
            'content': jsonable(content),
            'status': status,
            'visibility': visibility,
            'log': jsonable(log),
            'provider_message_id': provider_message_id,
        })
        self._touch_conversation(db, conversation_id)
        db.commit()
        db.refresh(row)
        return row

    def update_event(self, db: Session, message_id: UUID, **fields: Any) -> Message | None:
        payload = dict(fields)
        if 'content' in payload:
            payload['content'] = jsonable(payload['content'])
        if 'log' in payload:
            payload['log'] = jsonable(payload['log'])
        payload['updated_at'] = datetime.now()
        return self.update(db, message_id, payload)

    def append_content_text(self, db: Session, message_id: UUID, text: str) -> Message | None:
        row = self.get(db, message_id)
        if row is None:
            return None
        content = dict(row.content or {})
        existing = content.get('text') or ''
        content['text'] = f'{existing}{text}'
        row.content = content
        row.updated_at = datetime.now()
        flag_modified(row, 'content')
        db.commit()
        db.refresh(row)
        return row

    def finish_turn(
        self,
        db: Session,
        user_message_id: UUID,
        status: str,
        log: dict | None = None,
        error_message: str | None = None,
    ) -> None:
        rows = self._turn_rows(db, user_message_id)
        if not rows:
            return

        now = datetime.now()
        conversation_id = rows[0].conversation_id
        open_statuses = {None, 'pending', 'running'}
        child_status = 'completed' if status == 'completed' else status

        for row in rows:
            row.updated_at = now
            if row.id == user_message_id:
                row.status = status
                if log is not None:
                    row.log = jsonable(log)
                    flag_modified(row, 'log')
                if error_message:
                    content = dict(row.content or {})
                    content['error'] = error_message
                    row.content = content
                    flag_modified(row, 'content')
            elif row.status in open_statuses:
                row.status = child_status

        self._touch_conversation(db, conversation_id)
        db.commit()


messages_ops = MessagesDBOperations()
