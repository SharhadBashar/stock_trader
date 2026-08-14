from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes = True)

    id: UUID
    user_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
