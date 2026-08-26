from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic_ai.messages import (
    ModelMessage,
    ModelMessagesTypeAdapter,
    ModelRequest,
    ModelResponse,
    RetryPromptPart,
    SystemPromptPart,
    TextPart,
    ThinkingPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from core.common.agent_trace import TurnTrace, jsonable, parse_tool_args
from db.base_operations import BaseDBOperations
from db.models.conversations import Conversation
from db.models.messages import Message


def dump_payload(message: ModelMessage) -> dict:
    return ModelMessagesTypeAdapter.dump_python([message], mode = 'json')[0]


def message_kind(message: ModelMessage) -> str:
    if isinstance(message, ModelResponse):
        return 'response'
    return 'request'


def message_role(message: ModelMessage) -> str:
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


def display_content(message: ModelMessage) -> str | None:
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


def run_id_of(message: ModelMessage) -> str | None:
    run_id = getattr(message, 'run_id', None)
    if run_id is None:
        return None
    return str(run_id)


def message_thinking(message: ModelMessage) -> str | None:
    if not isinstance(message, ModelResponse):
        return getattr(message, 'thinking', None)
    texts = [
        part.content
        for part in message.parts
        if isinstance(part, ThinkingPart) and part.content
    ]
    if texts:
        return '\n'.join(texts)
    return getattr(message, 'thinking', None)


def message_tools_called(message: ModelMessage) -> list[dict[str, Any]] | None:
    if not isinstance(message, ModelResponse):
        return None
    tools = []
    for part in message.parts:
        if not isinstance(part, ToolCallPart):
            continue
        args = parse_tool_args(part.args)
        called_agent = args.get('agent_name') if isinstance(args, dict) else None
        tools.append({
            'tool_id': part.tool_call_id,
            'tool_name': part.tool_name,
            'args': args,
            'called_agent': called_agent,
        })
    return tools or None


def message_tool_responses(message: ModelMessage) -> list[dict[str, Any]] | None:
    if not isinstance(message, ModelRequest):
        return None
    responses = []
    for part in message.parts:
        if isinstance(part, ToolReturnPart):
            responses.append({
                'tool_id': part.tool_call_id,
                'tool_name': part.tool_name,
                'content': jsonable(part.content),
                'status': 'success',
            })
        elif isinstance(part, RetryPromptPart):
            responses.append({
                'tool_id': getattr(part, 'tool_call_id', None),
                'tool_name': getattr(part, 'tool_name', None),
                'content': jsonable(
                    getattr(part, 'content', None) or getattr(part, 'model_response', None)
                ),
                'status': 'error',
            })
    return responses or None


def infer_agent_name(message: ModelMessage, root_agent: str | None) -> str | None:
    role = message_role(message)
    if role == 'user':
        return None
    tools = message_tools_called(message) or []
    for tool in tools:
        called = tool.get('called_agent')
        if called:
            return root_agent
    responses = message_tool_responses(message) or []
    for response in responses:
        if response.get('tool_name') == 'delegate_task':
            return root_agent
    if role in {'assistant', 'tool', 'system'}:
        return root_agent
    return None


def infer_model_name(message: ModelMessage) -> str | None:
    return getattr(message, 'model_name', None)


def turn_summary(trace: TurnTrace | None) -> dict[str, Any]:
    if trace is None:
        return {
            'agents_called': None,
            'agent_steps': None,
            'tools_called': None,
            'tool_responses': None,
            'thinking': None,
        }
    return {
        'agents_called': jsonable(trace.agents_called()) or None,
        'agent_steps': jsonable(trace.steps) or None,
        'tools_called': jsonable(trace.tools_called()) or None,
        'tool_responses': jsonable(trace.tool_responses()) or None,
        'thinking': trace.thinking_text(),
    }


def history_row_fields(
    message: ModelMessage,
    *,
    user_query: str,
    root_agent: str | None,
    is_final: bool,
    include_summary: bool,
    trace: TurnTrace | None,
    latency_ms: int | None,
) -> dict[str, Any]:
    if include_summary:
        summary = turn_summary(trace)
    else:
        summary = {
            'agents_called': None,
            'agent_steps': None,
            'tools_called': message_tools_called(message),
            'tool_responses': message_tool_responses(message),
            'thinking': message_thinking(message),
        }
    return {
        'kind': message_kind(message),
        'role': message_role(message),
        'payload': dump_payload(message),
        'display_content': display_content(message),
        'run_id': run_id_of(message),
        'user_query': user_query,
        'agent_name': infer_agent_name(message, root_agent),
        'model_name': infer_model_name(message),
        'latency_ms': latency_ms if is_final else None,
        'is_final': is_final,
        **summary,
    }


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
            'payload': dump_payload(user_request),
            'display_content': query,
            'include_in_history': False,
            'status': 'pending',
            'run_id': run_id_of(user_request),
            'user_query': query,
            'agents_called': None,
            'agent_steps': None,
            'tools_called': None,
            'tool_responses': None,
            'thinking': None,
            'agent_name': None,
            'model_name': None,
            'latency_ms': None,
            'is_final': False,
        })

    def complete_turn(
        self,
        db: Session,
        conversation_id: UUID,
        user_message_id: UUID,
        new_messages: list[ModelMessage],
        trace: TurnTrace | None = None,
        root_agent: str | None = None,
    ) -> list[Message]:
        user_row = self.get(db, user_message_id)
        if not user_row:
            return []

        remaining = list(new_messages)
        if remaining and message_role(remaining[0]) == 'user':
            first = remaining[0]
            user_row.payload = dump_payload(first)
            user_row.display_content = display_content(first) or user_row.display_content
            user_row.kind = message_kind(first)
            user_row.role = 'user'
            user_row.run_id = run_id_of(first)
            remaining = remaining[1:]

        now = datetime.now()
        latency_ms = trace.latency_ms() if trace is not None else None
        summary = turn_summary(trace)
        last_index = len(remaining) - 1

        user_row.status = 'complete'
        user_row.include_in_history = True
        user_row.updated_at = now
        user_row.user_query = user_row.user_query or (trace.user_query if trace else None)
        user_row.agents_called = summary['agents_called']
        user_row.agent_steps = summary['agent_steps']
        user_row.tools_called = summary['tools_called']
        user_row.tool_responses = summary['tool_responses']
        user_row.thinking = summary['thinking']
        user_row.agent_name = None
        user_row.model_name = None
        user_row.latency_ms = None
        user_row.is_final = False

        sequence = self._next_sequence(db, conversation_id)
        last_assistant = None
        for index, message in enumerate(remaining):
            if message_role(message) == 'assistant':
                last_assistant = index
        for index, message in enumerate(remaining):
            is_final = index == last_assistant
            fields = history_row_fields(
                message,
                user_query = user_row.user_query or '',
                root_agent = root_agent,
                is_final = is_final,
                include_summary = is_final,
                trace = trace,
                latency_ms = latency_ms,
            )
            if is_final and not fields['model_name'] and trace is not None:
                for agent in reversed(trace.agents_called()):
                    if agent.get('name') == root_agent and agent.get('model'):
                        fields['model_name'] = agent['model']
                        break
            db.add(self.model(
                conversation_id = conversation_id,
                user_message_id = user_message_id,
                sequence = sequence,
                include_in_history = True,
                status = 'complete',
                created_at = now,
                updated_at = now,
                **fields,
            ))
            sequence += 1

        if last_index < 0:
            user_row.latency_ms = latency_ms

        self._touch_conversation(db, conversation_id)
        db.commit()
        return self._turn_rows(db, user_message_id)

    def fail_turn(
        self,
        db: Session,
        user_message_id: UUID,
        status: str,
        trace: TurnTrace | None = None,
    ) -> None:
        now = datetime.now()
        rows = self._turn_rows(db, user_message_id)
        if not rows:
            return
        conversation_id = rows[0].conversation_id
        summary = turn_summary(trace)
        latency_ms = trace.latency_ms() if trace is not None else None
        for row in rows:
            row.status = status
            row.include_in_history = False
            row.updated_at = now
            row.is_final = False
            if row.user_message_id is None:
                row.agents_called = summary['agents_called']
                row.agent_steps = summary['agent_steps']
                row.tools_called = summary['tools_called']
                row.tool_responses = summary['tool_responses']
                row.thinking = summary['thinking']
                row.latency_ms = latency_ms
        self._touch_conversation(db, conversation_id)
        db.commit()


messages_ops = MessagesDBOperations()
