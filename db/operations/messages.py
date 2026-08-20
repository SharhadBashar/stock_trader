from datetime import datetime
from uuid import UUID

from pydantic_ai.messages import (
    ModelMessage,
    ModelMessagesTypeAdapter,
    ModelRequest,
    ModelResponse,
    RetryPromptPart,
    SystemPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from db.base_operations import BaseDBOperations
from db.models.conversations import Conversation
from db.models.messages import Message


def _dump_payload(message: ModelMessage) -> dict:
    return ModelMessagesTypeAdapter.dump_python([message], mode = 'json')[0]


def _kind(message: ModelMessage) -> str:
    if isinstance(message, ModelResponse):
        return 'response'
    return 'request'


def _role(message: ModelMessage) -> str:
    if isinstance(message, ModelResponse):
        return 'assistant'
    if not isinstance(message, ModelRequest):
        return 'assistant'

    has_user = any(isinstance(part, UserPromptPart) for part in message.parts)
    has_tool = any(isinstance(part, (ToolReturnPart, RetryPromptPart)) for part in message.parts)
    has_system = any(isinstance(part, SystemPromptPart) for part in message.parts)
    if has_user:
        return 'user'
    if has_tool:
        return 'tool'
    if has_system:
        return 'system'
    return 'user'


def _part_text(content: object) -> str | None:
    if isinstance(content, str):
        return content
    if content is None:
        return None
    return str(content)


def _display_content(message: ModelMessage) -> str | None:
    if isinstance(message, ModelRequest):
        texts: list[str] = []
        for part in message.parts:
            if isinstance(part, UserPromptPart):
                text = _part_text(part.content)
                if text:
                    texts.append(text)
            elif isinstance(part, SystemPromptPart):
                text = _part_text(part.content)
                if text:
                    texts.append(text)
            elif isinstance(part, ToolReturnPart):
                text = _part_text(part.content)
                if text:
                    texts.append(text)
            elif isinstance(part, RetryPromptPart):
                text = _part_text(getattr(part, 'content', None) or getattr(part, 'model_response', None))
                if text:
                    texts.append(text)
        return '\n'.join(texts) if texts else None

    if isinstance(message, ModelResponse):
        texts = [
            part.content
            for part in message.parts
            if isinstance(part, TextPart) and part.content
        ]
        if texts:
            return ''.join(texts)
        tool_names = [
            part.tool_name
            for part in message.parts
            if isinstance(part, ToolCallPart) and part.tool_name
        ]
        if tool_names:
            return ', '.join(tool_names)
    return None


def _run_id(message: ModelMessage) -> str | None:
    run_id = getattr(message, 'run_id', None)
    if run_id is None:
        return None
    return str(run_id)


class MessagesDBOperations(BaseDBOperations[Message]):
    def __init__(self):
        super().__init__(Message)

    def _next_sequence(self, db: Session, conversation_id: UUID) -> int:
        max_sequence = (
            db.query(func.max(self.model.sequence))
            .filter(self.model.conversation_id == conversation_id)
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
            .order_by(self.model.sequence.asc())
            .all()
        )

    def _touch_conversation(self, db: Session, conversation_id: UUID) -> None:
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation:
            conversation.updated_at = datetime.now()

    def list_by_conversation(self, db: Session, conversation_id: UUID) -> list[Message]:
        return (
            db.query(self.model)
            .filter(self.model.conversation_id == conversation_id)
            .order_by(self.model.sequence.asc())
            .all()
        )

    def list_by_user_message_id(self, db: Session, user_message_id: UUID) -> list[Message]:
        return self._turn_rows(db, user_message_id)

    def get_history(self, db: Session, conversation_id: UUID) -> list[Message]:
        return (
            db.query(self.model)
            .filter(
                self.model.conversation_id == conversation_id,
                self.model.include_in_history.is_(True),
                self.model.status == 'complete',
            )
            .order_by(self.model.sequence.asc())
            .all()
        )

    def load_message_history(self, db: Session, conversation_id: UUID) -> list[ModelMessage]:
        rows = self.get_history(db, conversation_id)
        if not rows:
            return []
        return list(ModelMessagesTypeAdapter.validate_python(
            [row.payload for row in rows]
        ))

    def create_user_message(self, db: Session, conversation_id: UUID, query: str) -> Message:
        user_request = ModelRequest(parts = [UserPromptPart(content = query)])
        return self.create(db, {
            'conversation_id': conversation_id,
            'user_message_id': None,
            'sequence': self._next_sequence(db, conversation_id),
            'kind': 'request',
            'role': 'user',
            'payload': _dump_payload(user_request),
            'display_content': query,
            'include_in_history': False,
            'status': 'pending',
            'run_id': _run_id(user_request),
        })

    def complete_turn(
        self,
        db: Session,
        conversation_id: UUID,
        user_message_id: UUID,
        new_messages: list[ModelMessage],
    ) -> list[Message]:
        user_row = self.get(db, user_message_id)
        if not user_row:
            return []

        remaining = list(new_messages)
        if remaining and _role(remaining[0]) == 'user':
            first = remaining[0]
            user_row.payload = _dump_payload(first)
            user_row.display_content = _display_content(first) or user_row.display_content
            user_row.kind = _kind(first)
            user_row.role = 'user'
            user_row.run_id = _run_id(first)
            remaining = remaining[1:]

        sequence = self._next_sequence(db, conversation_id)
        now = datetime.now()
        user_row.status = 'complete'
        user_row.include_in_history = True
        user_row.updated_at = now

        for message in remaining:
            db.add(self.model(
                conversation_id = conversation_id,
                user_message_id = user_message_id,
                sequence = sequence,
                kind = _kind(message),
                role = _role(message),
                payload = _dump_payload(message),
                display_content = _display_content(message),
                include_in_history = True,
                status = 'complete',
                run_id = _run_id(message),
                created_at = now,
                updated_at = now,
            ))
            sequence += 1

        self._touch_conversation(db, conversation_id)
        db.commit()
        return self._turn_rows(db, user_message_id)

    def fail_turn(self, db: Session, user_message_id: UUID, status: str) -> None:
        now = datetime.now()
        rows = self._turn_rows(db, user_message_id)
        if not rows:
            return
        conversation_id = rows[0].conversation_id
        for row in rows:
            row.status = status
            row.include_in_history = False
            row.updated_at = now
        self._touch_conversation(db, conversation_id)
        db.commit()

    def exclude_turn(self, db: Session, user_message_id: UUID) -> list[Message]:
        now = datetime.now()
        rows = self._turn_rows(db, user_message_id)
        if not rows:
            return []
        conversation_id = rows[0].conversation_id
        for row in rows:
            row.include_in_history = False
            row.updated_at = now
        self._touch_conversation(db, conversation_id)
        db.commit()
        return self._turn_rows(db, user_message_id)


messages_ops = MessagesDBOperations()
