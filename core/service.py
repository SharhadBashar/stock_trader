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

logger = logging.getLogger(__name__)


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
            async for fragment in stream(query):
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
async def stream(query: str) -> AsyncGenerator[SSEFragment]:
    logfire = get_logfire()
    current_text_part_id: str | None = None
    collected_output = ''

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
                            yield ChatDoneEvent(final_output = final_output)

                        case _:
                            raise TypeError(f'Unhandled event type: {type(event).__name__}')

        except asyncio.CancelledError:
            logger.info('Client disconnected mid-stream')
            raise
        except pydantic_ai_exceptions.UsageLimitExceeded as e:
            logger.exception('LLM usage limit exceeded')
            yield ErrorEvent(error_type = 'usage_limit_exceeded', message = str(e))
        except Exception as e:
            logger.exception('Error in stream')
            yield ErrorEvent(message = str(e))
