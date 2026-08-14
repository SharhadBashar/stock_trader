from uuid import UUID

from pydantic import BaseModel


class CreateConversationRequest(BaseModel):
    user_id: UUID
    query: str


class UpdateConversationRequest(BaseModel):
    title: str
