from fastapi import APIRouter

from app.v0.router import v0_router


api_router = APIRouter()

api_router.include_router(v0_router, prefix = '/v0', tags = ['API v0'])
