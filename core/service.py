import asyncio
import logging
import uuid

from collections.abc import AsyncGenerator

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
from pydantic_ai.messages import ModelMessage
from db.base import get_db_session
from db.operations.messages import messages_ops

logger = logging.getLogger(__name__)


def _complete_turn(
    conversation_id: uuid.UUID | None,
    user_message_id: uuid.UUID | None,
    new_messages: list[ModelMessage],
) -> None:
    if conversation_id is None or user_message_id is None:
        return
    try:
        with get_db_session() as db:
            messages_ops.complete_turn(db, conversation_id, user_message_id, new_messages)
    except Exception:
        logger.exception('Failed to persist conversation messages')


def _fail_turn(user_message_id: uuid.UUID | None, status: str) -> None:
    if user_message_id is None:
        return
    try:
        with get_db_session() as db:
            messages_ops.fail_turn(db, user_message_id, status)
    except Exception:
        logger.exception('Failed to mark conversation turn as %s', status)


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
    user_message_id: uuid.UUID,
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
            async for fragment in stream(
                query,
                conversation_id = conversation_id,
                user_message_id = user_message_id,
            ):
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
    user_message_id: uuid.UUID | None = None,
) -> AsyncGenerator[SSEFragment]:
    logfire = get_logfire()
    current_text_part_id: str | None = None
    collected_output = ''
    turn_persisted = False

    with logfire.span('{query}', query = query):
        try:
            async with orchestrator_agent.run_stream_events(query) as event_stream:
                async for event in event_stream:
                    match event:
                        case PartStartEvent():
                            match event.part:
                                case TextPart(content = content):
                                    current_text_part_id = uuid.uuid4().hex
                                    collected_output += content
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
                                    collected_output += delta
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

                        case FinalResultEvent():
                            logger.debug('Skipping FinalResultEvent')

                        case FunctionToolCallEvent():
                            yield ToolStartEvent(
                                tool_id = event.tool_call_id,
                                name = event.part.tool_name,
                                args = event.part.args,
                            )

                        case FunctionToolResultEvent():
                            match event.part:
                                case ToolReturnPart():
                                    yield ToolEndEvent(tool_id = event.tool_call_id, status = 'success')
                                case RetryPromptPart():
                                    logger.warning(
                                        'Tool execution resulted in RetryPromptPart: %s',
                                        event.part,
                                    )
                                    yield ToolEndEvent(tool_id = event.tool_call_id, status = 'error')
                                case _:
                                    raise TypeError(
                                        f'Unhandled FunctionToolResultEvent.part type: {type(event.part).__name__}'
                                    )

                        case AgentRunResultEvent():
                            final_output = str(event.result.output) if event.result.output else collected_output
                            logfire.info(
                                'Final Output',
                                **final_output_attributes(query, final_output),
                            )
                            _complete_turn(
                                conversation_id,
                                user_message_id,
                                event.result.new_messages(),
                            )
                            turn_persisted = True
                            yield ChatDoneEvent(final_output = final_output)

                        case _:
                            raise TypeError(f'Unhandled event type: {type(event).__name__}')

            if not turn_persisted:
                _fail_turn(user_message_id, 'error')

        except asyncio.CancelledError:
            logger.info('Client disconnected mid-stream')
            if not turn_persisted:
                _fail_turn(user_message_id, 'cancelled')
            raise
        except pydantic_ai_exceptions.UsageLimitExceeded as e:
            logger.exception('LLM usage limit exceeded')
            if not turn_persisted:
                _fail_turn(user_message_id, 'error')
            yield ErrorEvent(error_type = 'usage_limit_exceeded', message = str(e))
        except Exception as e:
            logger.exception('Error in stream')
            if not turn_persisted:
                _fail_turn(user_message_id, 'error')
            yield ErrorEvent(message = str(e))
