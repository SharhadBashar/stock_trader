from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes = True)

    id: UUID
    firebase_uuid: str
    email: str
    phone: str | None = None
    created_at: datetime
    last_login: datetime | None = None
