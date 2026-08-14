from pydantic import BaseModel, Field

class ConversationTitle(BaseModel):
    title: str = Field(..., description = 'The title of the conversation based on the users query', max_length = 100)
