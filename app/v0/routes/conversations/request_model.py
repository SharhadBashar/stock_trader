from uuid import UUID

from pydantic import BaseModel


class CreateConversationRequest(BaseModel):
    user_id: UUID
    title: str | None = None


class UpdateConversationRequest(BaseModel):
    title: str
