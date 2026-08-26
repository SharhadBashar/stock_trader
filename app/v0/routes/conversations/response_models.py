from datetime import datetime
from typing import Any
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


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes = True)

    id: UUID
    conversation_id: UUID
    user_message_id: UUID | None
    sequence: int
    kind: str
    role: str
    payload: dict[str, Any]
    display_content: str | None
    include_in_history: bool
    status: str
    run_id: str | None
    user_query: str | None
    agents_called: list[Any] | None
    agent_steps: list[Any] | None
    tools_called: list[Any] | None
    tool_responses: list[Any] | None
    thinking: str | None
    agent_name: str | None
    model_name: str | None
    latency_ms: int | None
    is_final: bool
    created_at: datetime
    updated_at: datetime
