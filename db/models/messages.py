from datetime import datetime
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    UUID,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB

from db.base import Base


class Message(Base):
    '''
        Table to store conversation actions
        Table Name: messages
        Each row is one action in a turn (user prompt, thinking, tool call,
        tool response, or assistant output). Which agents ran and what steps
        they took is the set of rows, not a list on a single row.
        Columns:
            id: [UUID] - PK
            conversation_id: [UUID] - FK to conversations.id
            user_message_id: [UUID] - FK to messages.id, NULL on the user prompt
            sequence: [Integer] - order within the conversation
            kind: [String] - request or response
            role: [String] - user, assistant, tool, or system
            payload: [JSONB] - one pydantic-ai ModelMessage
            display_content: [Text] - user prompt or joined text parts
            include_in_history: [Boolean] - whether this row is passed as message_history
            status: [String] - pending, complete, error, or cancelled
            run_id: [String] - pydantic-ai run_id
            user_query: [Text] - what the user asked in this turn
            agent_name: [String] - which agent performed this action, if any
            model_name: [String] - model used for this action
            thinking: [Text] - thinking for this action, if any
            tool_name: [String] - tool for this action, if this is a tool call or result
            tool_args: [JSONB] - tool arguments, if this action is a tool call
            tool_response: [JSONB] - tool result, if this action is a tool response
            latency_ms: [Integer] - total turn latency on the final output row
            is_final: [Boolean] - whether this action is the final output
            created_at: [DateTime]
            updated_at: [DateTime]
    '''

    __tablename__ = 'messages'
    __table_args__ = (
        UniqueConstraint('conversation_id', 'sequence', name = 'uq_messages_conversation_sequence'),
        Index('ix_messages_user_message_id', 'user_message_id'),
        Index(
            'ix_messages_history',
            'conversation_id',
            'sequence',
            postgresql_where = text('include_in_history IS TRUE'),
        ),
        Index('ix_messages_is_final', 'conversation_id', 'is_final'),
    )

    id = Column(UUID, primary_key = True, default = uuid.uuid4)
    conversation_id = Column(
        UUID,
        ForeignKey('conversations.id', ondelete = 'CASCADE'),
        nullable = False,
    )
    user_message_id = Column(
        UUID,
        ForeignKey('messages.id', ondelete = 'CASCADE'),
        nullable = True,
    )
    sequence = Column(Integer, nullable = False)
    kind = Column(String, nullable = False)
    role = Column(String, nullable = False)
    payload = Column(JSONB, nullable = False)
    display_content = Column(Text, nullable = True)
    include_in_history = Column(Boolean, nullable = False, default = True)
    status = Column(String, nullable = False)
    run_id = Column(String, nullable = True)
    user_query = Column(Text, nullable = True)
    agent_name = Column(String, nullable = True)
    model_name = Column(String, nullable = True)
    thinking = Column(Text, nullable = True)
    tool_name = Column(String, nullable = True)
    tool_args = Column(JSONB, nullable = True)
    tool_response = Column(JSONB, nullable = True)
    latency_ms = Column(Integer, nullable = True)
    is_final = Column(Boolean, nullable = False, default = False)
    created_at = Column(DateTime, nullable = False, default = datetime.now)
    updated_at = Column(DateTime, nullable = False, default = datetime.now)
