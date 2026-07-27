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

from core.orchestrator_agent.agent import orchestrator_agent
from core.common.observability.pydantic_logfire.instrument_logfire import instrument_logfire, get_logfire
from core.common.observability.pydantic_logfire.utils import final_output_attributes
from core.common.sse import (
    ChatDoneEvent,
    ErrorEvent,
    TextChunkEvent,
    TextPartEndEvent,
    ThinkingEvent,
    ToolEndEvent,
    ToolStartEvent,
)
from core.common.sse.fragments import SSEFragment

logger = logging.getLogger(__name__)


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
