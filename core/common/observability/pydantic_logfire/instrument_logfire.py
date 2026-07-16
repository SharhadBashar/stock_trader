import functools
import inspect
import uuid

from contextvars import ContextVar

import logfire

from settings import LOGFIRE_TOKEN
from core.common.observability.pydantic_logfire.types import InstrumentType


_logfire_context: ContextVar[logfire.Logfire] = ContextVar("logfire_context")


def get_logfire() -> logfire.Logfire:
    try:
        return _logfire_context.get()
    except LookupError as err:
        raise RuntimeError(
            "No logfire instance in context. Did you forget @instrument_logfire?"
        ) from err


def instrument_logfire(
    instrument_type: InstrumentType = InstrumentType.PYDANTIC_AI,
    project: str | None = None,
):
    def decorator(obj):
        def _configure_logfire(name: str):
            prefix = project if project else name.lower()
            service_name = (
                f"{prefix}-{str(uuid.uuid4())[:5]}" if prefix else str(uuid.uuid4())[:5]
            )
            logfire_instance = logfire.configure(
                token=LOGFIRE_TOKEN,
                service_name=service_name,
                scrubbing=False,
                local=True,
                metrics=logfire.MetricsOptions(collect_in_spans=True),
            )
            if instrument_type == InstrumentType.PYDANTIC_AI:
                logfire_instance.instrument_pydantic_ai(include_binary_content=False)
            elif instrument_type == InstrumentType.OPENAI:
                logfire_instance.instrument_openai()
            elif instrument_type == InstrumentType.ANTHROPIC:
                logfire_instance.instrument_anthropic()
            _logfire_context.set(logfire_instance)

        # for classes, wrap the __init__ method
        if inspect.isclass(obj):
            original_init = obj.__init__

            @functools.wraps(original_init)
            def init_logfire(self, *args, **kwargs):
                _configure_logfire(obj.__name__)
                original_init(self, *args, **kwargs)

            obj.__init__ = init_logfire

            return obj

        # for coroutine functions, wrap the function itself
        elif inspect.iscoroutinefunction(obj):

            @functools.wraps(obj)
            async def async_wrapper(*args, **kwargs):
                _configure_logfire(obj.__name__)
                return await obj(*args, **kwargs)

            return async_wrapper

        # for regular functions, wrap the function itself
        elif inspect.isfunction(obj):

            @functools.wraps(obj)
            def sync_wrapper(*args, **kwargs):
                _configure_logfire(obj.__name__)
                return obj(*args, **kwargs)

            return sync_wrapper

        else:
            raise ValueError(
                f"Object {obj.__name__} is not a class, function, or coroutine function"
            )

    return decorator
