from fastapi import APIRouter

from app.v0.routes.auth.route import auth_router
from app.v0.routes.trader.route import trader_router
from app.v0.routes.users.route import users_router

v0_router = APIRouter()

v0_router.include_router(auth_router, prefix = '/auth', tags = ['Auth'])
v0_router.include_router(trader_router, prefix = '/trader', tags = ['Trader'])
v0_router.include_router(users_router, prefix = '/users', tags = ['Users'])
