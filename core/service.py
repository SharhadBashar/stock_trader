import asyncio
import logging
import time
import uuid
from datetime import datetime

from collections.abc import AsyncGenerator
from typing import Any

from pydantic_ai import (
    AgentRunResultEvent,
    FinalResultEvent,
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
    ToolCallPartDelta,
    ToolReturnPart,
)
from pydantic_ai import exceptions as pydantic_ai_exceptions

from core.agents import conversation_agent
from core.agents.orchestrator.agent import orchestrator_agent
from core.agents.conversation.types import ConversationTitle
from core.common.observability.pydantic_logfire.instrument_logfire import instrument_logfire, get_logfire
from core.common.observability.pydantic_logfire.utils import final_output_attributes
from core.common.sse import (
    ChatDoneEvent,
    ConversationCreatedEvent,
    ErrorEvent,
    TextChunkEvent,
    TextPartEndEvent,
    ThinkingEvent,
    TitleEvent,
    ToolEndEvent,
    ToolStartEvent,
)
from core.common.sse.fragments import SSEFragment
from db.base import get_db_session
from db.models.messages import Message
from db.operations.messages import messages_ops, parse_tool_args

logger = logging.getLogger(__name__)


def _create_message(
    conversation_id: uuid.UUID | None,
    msg_type: str,
    content: dict | None,
    **kwargs: Any,
) -> Message | None:
    if conversation_id is None:
        return None
    if kwargs.get('role') != 'user' and kwargs.get('user_message_id') is None:
        return None
    with get_db_session() as db:
        return messages_ops.create_message(db, conversation_id, msg_type, content, **kwargs)


def _preserve_unfinished_turn(
    conversation_id: uuid.UUID | None,
    user_message_id: uuid.UUID | None,
    collected_output: str,
    status: str,
) -> None:
    if conversation_id is None or user_message_id is None:
        return
    if collected_output:
        _create_message(
            conversation_id,
            'text',
            {'text': collected_output},
            user_message_id = user_message_id,
            status = status,
            agent_name = orchestrator_agent.name,
        )
    with get_db_session() as db:
        messages_ops.update(db, user_message_id, {
            'status': status,
            'updated_at': datetime.now(),
        })


def _delegate_agent_name(tool_name: str, args: Any) -> str | None:
    parsed = parse_tool_args(args)
    if tool_name == 'delegate_task' and isinstance(parsed, dict):
        delegate = parsed.get('agent_name')
        if isinstance(delegate, str):
            return delegate
    return None


def _span_log(latency_seconds: float | None = None) -> dict[str, Any] | None:
    log: dict[str, Any] = {}
    if latency_seconds is not None:
        log['latency_seconds'] = round(latency_seconds, 3)
    try:
        from opentelemetry.trace import get_current_span

        span = get_current_span()
        ctx = span.get_span_context()
        if ctx.is_valid:
            log['span_id'] = format(ctx.span_id, '016x')
            log['trace_id'] = format(ctx.trace_id, '032x')
    except Exception:
        pass
    return log or None


@instrument_logfire(project = 'conversation_title')
async def generate_conversation_title(query: str) -> ConversationTitle:
    logfire = get_logfire()
    with logfire.span('{query}', query = query):
        result = await conversation_agent.run(query)
        return result.output


async def stream_conversation(
    query: str,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    title: str,
) -> AsyncGenerator[SSEFragment]:
    yield ConversationCreatedEvent(
        conversation_id = conversation_id,
        user_id = user_id,
        title = title,
    )

    queue: asyncio.Queue[SSEFragment | None] = asyncio.Queue()

    async def produce_title() -> None:
        try:
            generated = await generate_conversation_title(query)
            generated_title = generated.title.strip()
            if generated_title:
                await queue.put(TitleEvent(
                    title = generated_title,
                    conversation_id = conversation_id,
                ))
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception('Failed to generate conversation title')
        finally:
            await queue.put(None)

    async def produce_stream() -> None:
        try:
            async for fragment in stream(query, conversation_id = conversation_id):
                await queue.put(fragment)
        except asyncio.CancelledError:
            raise
        finally:
            await queue.put(None)

    title_task = asyncio.create_task(produce_title())
    stream_task = asyncio.create_task(produce_stream())
    producers_left = 2

    try:
        while producers_left:
            item = await queue.get()
            if item is None:
                producers_left -= 1
                continue
            yield item
    except asyncio.CancelledError:
        title_task.cancel()
        stream_task.cancel()
        raise
    finally:
        for task in (title_task, stream_task):
            if not task.done():
                task.cancel()
        await asyncio.gather(title_task, stream_task, return_exceptions = True)


@instrument_logfire(project = 'trader')
async def stream(
    query: str,
    conversation_id: uuid.UUID | None = None,
) -> AsyncGenerator[SSEFragment]:
    logfire = get_logfire()
    current_text_part_id: str | None = None
    current_collected_raw_output = ''
    tool_call_ids_to_tool_call_part: dict[str, FunctionToolCallEvent] = {}
    start_time = time.time()
    user_message_id: uuid.UUID | None = None
    if conversation_id is not None:
        user_message = _create_message(
            conversation_id,
            'text',
            {'text': query},
            role = 'user',
            status = 'pending',
        )
        if user_message is not None:
            user_message_id = user_message.id

    with logfire.span('{query}', query = query):
        try:
            async with orchestrator_agent.run_stream_events(query) as event_stream:
                async for event in event_stream:
                    match event:
                        case PartStartEvent():
                            match event.part:
                                case TextPart(content = content):
                                    current_text_part_id = uuid.uuid4().hex
                                    current_collected_raw_output += content
                                    yield TextChunkEvent(text = content, part_id = current_text_part_id)
                                case ThinkingPart(content = content):
                                    yield ThinkingEvent(thinking_content = content)
                                case ToolCallPart():
                                    logger.debug('Skipping tool call part start')
                                case _:
                                    raise TypeError(
                                        f'Unhandled PartStartEvent.part type: {type(event.part).__name__}'
                                    )

                        case PartDeltaEvent():
                            match event.delta:
                                case TextPartDelta(content_delta = delta):
                                    current_collected_raw_output += delta
                                    yield TextChunkEvent(text = delta, part_id = current_text_part_id)
                                case ThinkingPartDelta(content_delta = delta):
                                    yield ThinkingEvent(thinking_content = delta)
                                case ToolCallPartDelta():
                                    logger.debug('Skipping tool call part delta')
                                case _:
                                    raise TypeError(
                                        f'Unhandled PartDeltaEvent.delta type: {type(event.delta).__name__}'
                                    )

                        case PartEndEvent():
                            match event.part:
                                case TextPart():
                                    if current_text_part_id is not None:
                                        yield TextPartEndEvent(part_id = current_text_part_id)
                                        current_text_part_id = None
                                    if getattr(event, 'next_part_kind', None) is not None:
                                        _create_message(
                                            conversation_id,
                                            'text',
                                            {'text': event.part.content},
                                            user_message_id = user_message_id,
                                            status = 'completed',
                                            agent_name = orchestrator_agent.name,
                                        )
                                        current_collected_raw_output = ''

                        case FinalResultEvent():
                            logger.debug('Skipping FinalResultEvent')

                        case FunctionToolCallEvent():
                            tool_call_ids_to_tool_call_part[event.part.tool_call_id] = event
                            yield ToolStartEvent(
                                tool_id = event.tool_call_id,
                                name = event.part.tool_name,
                                args = event.part.args,
                            )

                        case FunctionToolResultEvent():
                            match event.part:
                                case ToolReturnPart() | RetryPromptPart():
                                    tool_call_event = tool_call_ids_to_tool_call_part[event.part.tool_call_id]
                                    _create_message(
                                        conversation_id,
                                        'tool_call',
                                        {'args': parse_tool_args(tool_call_event.part.args)},
                                        user_message_id = user_message_id,
                                        status = 'completed',
                                        call_id = tool_call_event.part.tool_call_id,
                                        tool_name = tool_call_event.part.tool_name,
                                        delegate_agent_name = _delegate_agent_name(
                                            tool_call_event.part.tool_name,
                                            tool_call_event.part.args,
                                        ),
                                        agent_name = orchestrator_agent.name,
                                    )
                                    if isinstance(event.part, ToolReturnPart):
                                        _create_message(
                                            conversation_id,
                                            'tool_result',
                                            {'result': parse_tool_args(event.part.content)},
                                            user_message_id = user_message_id,
                                            status = 'completed',
                                            call_id = event.tool_call_id,
                                            tool_name = event.part.tool_name,
                                            agent_name = orchestrator_agent.name,
                                        )
                                        yield ToolEndEvent(tool_id = event.tool_call_id, status = 'success')
                                    else:
                                        logger.warning(
                                            'Tool execution resulted in RetryPromptPart: %s',
                                            event.part,
                                        )
                                        _create_message(
                                            conversation_id,
                                            'tool_result',
                                            {
                                                'error': parse_tool_args(
                                                    getattr(event.part, 'content', None)
                                                    or getattr(event.part, 'model_response', None)
                                                ),
                                            },
                                            user_message_id = user_message_id,
                                            status = 'error',
                                            call_id = event.tool_call_id,
                                            tool_name = tool_call_event.part.tool_name,
                                            agent_name = orchestrator_agent.name,
                                        )
                                        yield ToolEndEvent(tool_id = event.tool_call_id, status = 'error')
                                case _:
                                    raise TypeError(
                                        f'Unhandled FunctionToolResultEvent.part type: {type(event.part).__name__}'
                                    )

                        case AgentRunResultEvent():
                            final_output = str(event.result.output) if event.result.output else current_collected_raw_output
                            logfire.info(
                                'Final Output',
                                **final_output_attributes(query, final_output),
                            )
                            model_name = getattr(
                                getattr(event.result, 'response', None),
                                'model_name',
                                None,
                            )
                            _create_message(
                                conversation_id,
                                'text',
                                {'text': final_output},
                                user_message_id = user_message_id,
                                status = 'completed',
                                agent_name = orchestrator_agent.name,
                                model = model_name,
                                log = _span_log(time.time() - start_time),
                            )
                            if user_message_id is not None:
                                with get_db_session() as db:
                                    messages_ops.update(db, user_message_id, {
                                        'status': 'completed',
                                        'updated_at': datetime.now(),
                                    })
                            yield ChatDoneEvent(final_output = final_output)

                        case _:
                            raise TypeError(f'Unhandled event type: {type(event).__name__}')

        except asyncio.CancelledError:
            logger.info('Client disconnected mid-stream')
            _preserve_unfinished_turn(
                conversation_id,
                user_message_id,
                current_collected_raw_output,
                'cancelled',
            )
            raise
        except pydantic_ai_exceptions.UsageLimitExceeded as e:
            logger.exception('LLM usage limit exceeded')
            _preserve_unfinished_turn(
                conversation_id,
                user_message_id,
                current_collected_raw_output,
                'error',
            )
            yield ErrorEvent(error_type = 'usage_limit_exceeded', message = str(e))
        except Exception as e:
            logger.exception('Error in stream')
            _preserve_unfinished_turn(
                conversation_id,
                user_message_id,
                current_collected_raw_output,
                'error',
            )
            yield ErrorEvent(message = str(e))
