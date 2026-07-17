from pydantic import BaseModel


class TradeRequest(BaseModel):
    query: str
