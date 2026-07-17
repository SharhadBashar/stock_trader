from fastapi import APIRouter

from app.v0.routes.trader.route import trader_router

v0_router = APIRouter()

v0_router.include_router(trader_router, prefix = '/trader', tags = ['Trader'])