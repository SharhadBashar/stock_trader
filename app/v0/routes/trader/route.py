import logging

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from app.v0.routes.trader.request_model import TradeRequest
from core.auth import get_current_user
from core.service import stream
from db.models import User

logger = logging.getLogger(__name__)

trader_router = APIRouter()


@trader_router.post('/chat', tags = ['Trader'])
async def chat(request: TradeRequest, current_user: User = Depends(get_current_user)):
    async def generate_sse_events():
        try:
            async for fragment in stream(request.query):
                yield fragment.to_sse().encode()
        except Exception:
            logger.exception('Error in SSE stream')
            raise

    return EventSourceResponse(generate_sse_events())
