from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CreateUserRequest(BaseModel):
    firebase_id: str
    name: str
    email: str
    phone: str | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes = True)

    id: UUID
    firebase_id: str
    name: str
    email: str
    phone: str | None
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
