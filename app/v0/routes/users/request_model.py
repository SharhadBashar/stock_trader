from pydantic import BaseModel


class CreateUserRequest(BaseModel):
    firebase_id: str
    name: str
    email: str
    phone: str | None = None
