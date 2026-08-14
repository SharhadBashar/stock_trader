from fastapi import FastAPI
import logfire

from app.api import api_router
from settings import validate_environment

validate_environment()
logfire.configure()
app = FastAPI()
logfire.instrument_fastapi(app)

app.include_router(api_router)


@app.get('/')
async def root():
    return {'message': 'Welcome to AI Stock Trader'}


@app.get('/status')
async def status():
    return {'message': 'AI Stock Trader is up and running 😊'}
