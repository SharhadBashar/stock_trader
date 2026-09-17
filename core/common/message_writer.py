from __future__ import annotations

import logging
import time
from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from db.base import get_db_session
from db.models.messages import Message
from db.operations.messages import MessagesDBOperations, messages_ops, parse_tool_args

logger = logging.getLogger(__name__)

SessionFactory = Callable[[], AbstractContextManager[Session]]


def current_span_log() -> dict[str, str] | None:
    try:
        from opentelemetry.trace import get_current_span

        span = get_current_span()
        ctx = span.get_span_context()
        if not ctx.is_valid:
            return None
        return {
            'span_id': format(ctx.span_id, '016x'),
            'trace_id': format(ctx.trace_id, '032x'),
        }
    except Exception:
        return None


class StreamMessageWriter:
    '''Persist one conversation turn as Message rows while the agent streams.'''

    def __init__(
        self,
        conversation_id: UUID | None,
        user_message_id: UUID | None,
        *,
        agent_name: str | None = None,
        parent_agent_name: str | None = None,
        model: str | None = None,
        ops: MessagesDBOperations | None = None,
        session_factory: SessionFactory | None = None,
    ) -> None:
        self.conversation_id = conversation_id
        self.user_message_id = user_message_id
        self.agent_name = agent_name
        self.parent_agent_name = parent_agent_name
        self.model = model
        self.enabled = conversation_id is not None and user_message_id is not None
        self._ops = ops or messages_ops
        self._session_factory = session_factory or get_db_session
        self._thinking_id: UUID | None = None
        self._text_id: UUID | None = None
        self._last_id: UUID | None = user_message_id
        self._call_ids: dict[str, UUID] = {}
        self._wrote_output = False
        self._started_at = time.perf_counter()
        self.finished = False

    def _parent_id(self) -> UUID | None:
        return self._last_id or self.user_message_id

    def _row_log(self, extra: dict[str, Any] | None = None) -> dict[str, Any] | None:
        log = dict(current_span_log() or {})
        if extra:
            log.update(extra)
        return log or None

    def _run(self, fn: Callable[[Session], Any]) -> Any:
        if not self.enabled:
            return None
        try:
            with self._session_factory() as db:
                return fn(db)
        except Exception:
            logger.exception('Failed to persist conversation message')
            return None

    def _remember(self, row: Message | None) -> UUID | None:
        if row is None:
            return None
        self._last_id = row.id
        return row.id

    def start_thinking(self, text: str) -> None:
        if self._thinking_id is not None:
            self.end_thinking()
        row = self._run(lambda db: self._ops.append_event(
            db,
            conversation_id = self.conversation_id,
            user_message_id = self.user_message_id,
            role = 'assistant',
            msg_type = 'thinking',
            content = {'text': text or ''},
            status = 'running',
            agent_name = self.agent_name,
            parent_agent_name = self.parent_agent_name,
            model = self.model,
            parent_message_id = self._parent_id(),
            log = self._row_log(),
        ))
        self._thinking_id = self._remember(row)

    def append_thinking(self, text: str) -> None:
        if not text:
            return
        if self._thinking_id is None:
            self.start_thinking(text)
            return
        self._run(lambda db: self._ops.append_content_text(db, self._thinking_id, text))

    def end_thinking(self) -> None:
        if self._thinking_id is None:
            return
        thinking_id = self._thinking_id
        self._run(lambda db: self._ops.update_event(db, thinking_id, status = 'completed'))
        self._thinking_id = None

    def start_text(self, text: str, part_id: str | None = None) -> None:
        if self._text_id is not None:
            self.end_text()
        if self._thinking_id is not None:
            self.end_thinking()
        row = self._run(lambda db: self._ops.append_event(
            db,
            conversation_id = self.conversation_id,
            user_message_id = self.user_message_id,
            role = 'assistant',
            msg_type = 'agent_output',
            content = {'text': text or ''},
            status = 'running',
            agent_name = self.agent_name,
            parent_agent_name = self.parent_agent_name,
            model = self.model,
            parent_message_id = self._parent_id(),
            provider_message_id = part_id,
            log = self._row_log(),
        ))
        self._text_id = self._remember(row)
        if self._text_id is not None:
            self._wrote_output = True

    def append_text(self, text: str) -> None:
        if not text:
            return
        if self._text_id is None:
            self.start_text(text)
            return
        self._run(lambda db: self._ops.append_content_text(db, self._text_id, text))

    def end_text(self) -> None:
        if self._text_id is None:
            return
        text_id = self._text_id
        self._run(lambda db: self._ops.update_event(db, text_id, status = 'completed'))
        self._text_id = None

    def tool_call(self, call_id: str, name: str, args: Any = None) -> None:
        if self._thinking_id is not None:
            self.end_thinking()
        parsed_args = parse_tool_args(args)
        delegate_agent_name = None
        if name == 'delegate_task' and isinstance(parsed_args, dict):
            delegate = parsed_args.get('agent_name')
            if isinstance(delegate, str):
                delegate_agent_name = delegate
        row = self._run(lambda db: self._ops.append_event(
            db,
            conversation_id = self.conversation_id,
            user_message_id = self.user_message_id,
            role = 'assistant',
            msg_type = 'tool_call',
            content = {'args': parsed_args},
            status = 'running',
            call_id = call_id,
            agent_name = self.agent_name,
            parent_agent_name = self.parent_agent_name,
            model = self.model,
            tool_name = name,
            delegate_agent_name = delegate_agent_name,
            parent_message_id = self._parent_id(),
            log = self._row_log(),
        ))
        row_id = self._remember(row)
        if row_id is not None:
            self._call_ids[call_id] = row_id

    def tool_result(
        self,
        call_id: str,
        name: str | None,
        content: Any,
        status: str,
    ) -> None:
        parent_id = self._call_ids.get(call_id) or self._parent_id()
        row_status = 'completed' if status == 'success' else 'error'
        row = self._run(lambda db: self._ops.append_event(
            db,
            conversation_id = self.conversation_id,
            user_message_id = self.user_message_id,
            role = 'tool',
            msg_type = 'tool_result',
            content = {'result': parse_tool_args(content)},
            status = row_status,
            call_id = call_id,
            agent_name = self.agent_name,
            parent_agent_name = self.parent_agent_name,
            model = self.model,
            tool_name = name,
            parent_message_id = parent_id,
            log = self._row_log(),
        ))
        self._remember(row)
        tool_call_id = self._call_ids.get(call_id)
        if tool_call_id is not None:
            self._run(lambda db: self._ops.update_event(db, tool_call_id, status = row_status))

    def complete(self, final_output: str | None = None) -> None:
        if self.finished:
            return
        self.end_thinking()
        self.end_text()
        if final_output and not self._wrote_output:
            row = self._run(lambda db: self._ops.append_event(
                db,
                conversation_id = self.conversation_id,
                user_message_id = self.user_message_id,
                role = 'assistant',
                msg_type = 'agent_output',
                content = {'text': final_output},
                status = 'completed',
                agent_name = self.agent_name,
                parent_agent_name = self.parent_agent_name,
                model = self.model,
                parent_message_id = self._parent_id(),
                log = self._row_log(),
            ))
            self._remember(row)
        self._finish('completed')

    def fail(self, status: str, error_message: str | None = None) -> None:
        if self.finished:
            return
        self._finish(status, error_message = error_message)

    def _finish(self, status: str, error_message: str | None = None) -> None:
        if not self.enabled or self.user_message_id is None:
            self.finished = True
            return
        log = self._row_log({
            'latency_seconds': round(time.perf_counter() - self._started_at, 3),
        })
        user_message_id = self.user_message_id
        self._run(lambda db: self._ops.finish_turn(
            db,
            user_message_id,
            status,
            log = log,
            error_message = error_message,
        ))
        self.finished = True
