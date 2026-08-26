from __future__ import annotations

from collections.abc import AsyncIterable
from contextvars import ContextVar, Token
from datetime import datetime, timezone
import json
import time
from typing import Any

from pydantic_ai import (
    AgentRunResultEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartEndEvent,
    PartStartEvent,
    RetryPromptPart,
    TextPart,
    TextPartDelta,
    ThinkingPart,
    ThinkingPartDelta,
    ToolCallPart,
    ToolReturnPart,
)
from pydantic_ai_harness.subagents import SubAgents


_current_trace: ContextVar[TurnTrace | None] = ContextVar('current_message_trace', default = None)


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


def model_name_of(model: Any) -> str | None:
    if model is None:
        return None
    return getattr(model, 'model_name', None) or getattr(model, 'name', None)


def agent_name_of(agent: Any) -> str | None:
    if agent is None:
        return None
    return getattr(agent, 'name', None)


class TurnTrace:
    def __init__(self, user_query: str, root_agent: str | None = None, root_model: str | None = None):
        self.user_query = user_query
        self.started_at = time.perf_counter()
        self.steps: list[dict[str, Any]] = []
        self._buffers: dict[str, dict[str, str]] = {}
        self._agents: dict[str, str | None] = {}
        if root_agent:
            self.add_agent(root_agent, root_model)

    def latency_ms(self) -> int:
        return max(0, int((time.perf_counter() - self.started_at) * 1000))

    def add_agent(self, name: str, model: str | None = None) -> None:
        if not name:
            return
        if name not in self._agents or (model and not self._agents.get(name)):
            self._agents[name] = model

    def agents_called(self) -> list[dict[str, Any]]:
        called = [
            {'name': name, 'model': model}
            for name, model in self._agents.items()
        ]
        for step in self.steps:
            called_agent = step.get('called_agent')
            if called_agent and all(item['name'] != called_agent for item in called):
                called.append({'name': called_agent, 'model': None})
        return called

    def tools_called(self) -> list[dict[str, Any]]:
        return [step for step in self.steps if step.get('type') == 'tool_call']

    def tool_responses(self) -> list[dict[str, Any]]:
        return [step for step in self.steps if step.get('type') == 'tool_result']

    def thinking_text(self) -> str | None:
        parts: list[str] = []
        for step in self.steps:
            if step.get('type') != 'thinking':
                continue
            content = step.get('content')
            if not content:
                continue
            agent = step.get('agent') or 'unknown'
            parts.append(f'[{agent}]\n{content}')
        return '\n\n'.join(parts) if parts else None

    def add_step(self, step: dict[str, Any]) -> None:
        agent = step.get('agent')
        if isinstance(agent, str) and agent:
            self.add_agent(agent, step.get('model'))
        called_agent = step.get('called_agent')
        if isinstance(called_agent, str) and called_agent:
            self.add_agent(called_agent)
        self.steps.append(step)

    def _buffer(self, key: str, agent_name: str | None = None, model_name: str | None = None) -> dict[str, str]:
        buf = self._buffers.setdefault(key, {
            'thinking': '',
            'text': '',
            'agent': agent_name or '',
            'model': model_name or '',
        })
        if agent_name:
            buf['agent'] = agent_name
        if model_name:
            buf['model'] = model_name
        return buf

    def flush(self) -> None:
        now = datetime.now(timezone.utc).isoformat()
        for buf in self._buffers.values():
            if buf['thinking']:
                self.add_step({
                    'type': 'thinking',
                    'agent': buf.get('agent') or None,
                    'model': buf.get('model') or None,
                    'content': buf['thinking'],
                    'ts': now,
                })
                buf['thinking'] = ''
            if buf['text']:
                self.add_step({
                    'type': 'text',
                    'agent': buf.get('agent') or None,
                    'model': buf.get('model') or None,
                    'content': buf['text'],
                    'ts': now,
                })
                buf['text'] = ''

    def record(
        self,
        event: Any,
        *,
        agent_name: str | None,
        model_name: str | None = None,
        buffer_key: str = 'root',
        run_id: str | None = None,
        run_step: int | None = None,
    ) -> None:
        if agent_name:
            self.add_agent(agent_name, model_name)

        buf = self._buffer(buffer_key, agent_name, model_name)
        now = datetime.now(timezone.utc).isoformat()
        base = {
            'agent': agent_name,
            'model': model_name,
            'run_id': run_id,
            'run_step': run_step,
            'ts': now,
        }

        match event:
            case PartStartEvent():
                match event.part:
                    case ThinkingPart(content = content):
                        buf['thinking'] = content or ''
                    case TextPart(content = content):
                        buf['text'] = content or ''
                    case ToolCallPart():
                        return
                    case _:
                        return

            case PartDeltaEvent():
                match event.delta:
                    case ThinkingPartDelta(content_delta = delta):
                        buf['thinking'] += delta or ''
                    case TextPartDelta(content_delta = delta):
                        buf['text'] += delta or ''
                    case _:
                        return

            case PartEndEvent():
                match event.part:
                    case ThinkingPart(content = content):
                        thinking = content or buf['thinking']
                        buf['thinking'] = ''
                        if thinking:
                            self.add_step({
                                **base,
                                'type': 'thinking',
                                'content': thinking,
                            })
                    case TextPart(content = content):
                        text = content or buf['text']
                        buf['text'] = ''
                        if text:
                            self.add_step({
                                **base,
                                'type': 'text',
                                'content': text,
                            })
                    case _:
                        return

            case FunctionToolCallEvent():
                args = parse_tool_args(event.part.args)
                called_agent = None
                task = None
                if isinstance(args, dict):
                    called_agent = args.get('agent_name')
                    task = args.get('task')
                    if called_agent:
                        self.add_agent(str(called_agent))
                self.add_step({
                    **base,
                    'type': 'tool_call',
                    'tool_id': event.tool_call_id,
                    'tool_name': event.part.tool_name,
                    'args': args,
                    'called_agent': called_agent,
                    'task': task,
                })
                if called_agent:
                    self.add_step({
                        **base,
                        'type': 'agent_call',
                        'tool_id': event.tool_call_id,
                        'called_agent': called_agent,
                        'task': task,
                    })

            case FunctionToolResultEvent():
                status = 'success'
                content: Any = None
                tool_name = getattr(event.part, 'tool_name', None)
                match event.part:
                    case ToolReturnPart():
                        content = jsonable(event.part.content)
                    case RetryPromptPart():
                        status = 'error'
                        content = jsonable(
                            getattr(event.part, 'content', None)
                            or getattr(event.part, 'model_response', None)
                        )
                    case _:
                        content = jsonable(getattr(event.part, 'content', None))
                self.add_step({
                    **base,
                    'type': 'tool_result',
                    'tool_id': event.tool_call_id,
                    'tool_name': tool_name,
                    'content': content,
                    'status': status,
                })

            case AgentRunResultEvent():
                output = event.result.output if event.result is not None else None
                self.add_step({
                    **base,
                    'type': 'final',
                    'content': str(output) if output is not None else None,
                    'is_final': True,
                })

            case _:
                return


def current_trace() -> TurnTrace | None:
    return _current_trace.get()


def begin_turn(user_query: str, root_agent: str | None = None, root_model: str | None = None) -> tuple[TurnTrace, Token]:
    trace = TurnTrace(user_query, root_agent = root_agent, root_model = root_model)
    token = _current_trace.set(trace)
    return trace, token


def end_turn(token: Token) -> None:
    _current_trace.reset(token)


def context_model_name(ctx: Any) -> str | None:
    return model_name_of(getattr(ctx, 'model', None))


def context_agent_name(ctx: Any) -> str | None:
    return agent_name_of(getattr(ctx, 'agent', None))


async def record_subagent_events(ctx: Any, events: AsyncIterable[Any]) -> None:
    trace = current_trace()
    agent_name = context_agent_name(ctx)
    model_name = context_model_name(ctx)
    run_id = getattr(ctx, 'run_id', None)
    buffer_key = str(run_id or id(ctx))
    if trace is not None and agent_name:
        trace.add_agent(agent_name, model_name)
    async for event in events:
        if trace is None:
            continue
        trace.record(
            event,
            agent_name = agent_name,
            model_name = model_name,
            buffer_key = buffer_key,
            run_id = str(run_id) if run_id is not None else None,
            run_step = getattr(ctx, 'run_step', None),
        )


def traced_sub_agents(agents: list[Any]) -> SubAgents:
    return SubAgents(
        agents,
        event_stream_handler = record_subagent_events,
    )
