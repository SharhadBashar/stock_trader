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
        Table to store conversation messages
        Table Name: messages
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
            user_query: [Text] - the original user question for this turn
            agents_called: [JSONB] - agents invoked during the turn
            agent_steps: [JSONB] - ordered steps each agent took
            tools_called: [JSONB] - tool calls (name, args, agent, model)
            tool_responses: [JSONB] - tool results (content, status, agent)
            thinking: [Text] - model thinking for this row or the full turn
            agent_name: [String] - which agent produced this row, if any
            model_name: [String] - model used for this row or the final output
            latency_ms: [Integer] - total turn latency on the final message
            is_final: [Boolean] - whether this row is the final assistant output
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
    agents_called = Column(JSONB, nullable = True)
    agent_steps = Column(JSONB, nullable = True)
    tools_called = Column(JSONB, nullable = True)
    tool_responses = Column(JSONB, nullable = True)
    thinking = Column(Text, nullable = True)
    agent_name = Column(String, nullable = True)
    model_name = Column(String, nullable = True)
    latency_ms = Column(Integer, nullable = True)
    is_final = Column(Boolean, nullable = False, default = False)
    created_at = Column(DateTime, nullable = False, default = datetime.now)
    updated_at = Column(DateTime, nullable = False, default = datetime.now)
