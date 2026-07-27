import json

from typing import Any, Protocol

from sse_starlette.sse import ServerSentEvent


class SSEFragment(Protocol):
    def to_sse(self) -> ServerSentEvent: ...


class ThinkingEvent(SSEFragment):
    def __init__(self, thinking_content: str) -> None:
        self.thinking_content = thinking_content

    def to_sse(self) -> ServerSentEvent:
        return ServerSentEvent(
            data = json.dumps({'thinking_content': self.thinking_content}),
            event = 'thinking',
        )


class TextChunkEvent(SSEFragment):
    def __init__(self, text: str, part_id: str | None = None) -> None:
        self.text = text
        self.part_id = part_id

    def to_sse(self) -> ServerSentEvent:
        data: dict[str, Any] = {'text': self.text}
        if self.part_id is not None:
            data['part_id'] = self.part_id
        return ServerSentEvent(
            data = json.dumps(data),
            event = 'text',
        )


class TextPartEndEvent(SSEFragment):
    def __init__(self, part_id: str) -> None:
        self.part_id = part_id

    def to_sse(self) -> ServerSentEvent:
        return ServerSentEvent(
            data = json.dumps({'part_id': self.part_id}),
            event = 'text_part_end',
        )


class ToolStartEvent(SSEFragment):
    def __init__(self, tool_id: str, name: str, args: Any = None) -> None:
        self.tool_id = tool_id
        self.name = name
        self.args = args

    def to_sse(self) -> ServerSentEvent:
        data: dict[str, Any] = {
            'id': self.tool_id,
            'name': self.name,
        }
        if self.args is not None:
            if isinstance(self.args, str):
                try:
                    data['args'] = json.loads(self.args)
                except json.JSONDecodeError:
                    data['args'] = self.args
            else:
                data['args'] = self.args
        return ServerSentEvent(
            data = json.dumps(data),
            event = 'tool_start',
        )


class ToolEndEvent(SSEFragment):
    def __init__(self, tool_id: str, status: str = 'success') -> None:
        self.tool_id = tool_id
        self.status = status

    def to_sse(self) -> ServerSentEvent:
        return ServerSentEvent(
            data = json.dumps({
                'id': self.tool_id,
                'status': self.status,
            }),
            event = 'tool_end',
        )


class ChatDoneEvent(SSEFragment):
    def __init__(self, final_output: str ) -> None:
        self.final_output = final_output
    def to_sse(self) -> ServerSentEvent:
        return ServerSentEvent(
            data = json.dumps({'final_output': self.final_output}),
            event = 'done',
        )


class ErrorEvent(SSEFragment):
    def __init__(
        self,
        message: str,
        error_type: str | None = None,
    ) -> None:
        self.message = message
        self.error_type = error_type

    def to_sse(self) -> ServerSentEvent:
        error_data = {'message': self.message}
        if self.error_type:
            error_data['error_type'] = self.error_type
        return ServerSentEvent(
            data = json.dumps(error_data),
            event = 'error',
        )
