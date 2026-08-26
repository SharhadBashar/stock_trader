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
        Table to store conversation actions, shaped like Cursor composer bubbles.

        Table Name: messages
        Each row is one action (user prompt, thinking, tool call, or assistant
        text). A user turn is the rows that share user_message_id. Parallel
        agents are separate rows with different agent_name / run_id, the same
        parent_id (the action that spawned them), and overlapping
        started_at / ended_at. sequence is append order only, not causality.

        Cursor mapping:
            conversation_id     composerId
            id                  bubbleId
            user_message_id     requestId / user bubble that started the turn
            parent_id           bubble that spawned this action (delegate / subagent)
            role / kind         type 1 user, type 2 assistant
            display_content     text
            thinking            thinking.text
            thinking_duration_ms thinkingDurationMs
            tool_call_id        toolFormerData.toolCallId
            tool_name           toolFormerData.name
            tool_args           toolFormerData.params / rawArgs
            tool_response       toolFormerData.result
            tool_status         toolFormerData.status (running | completed | error)
            agent_name          agent_id
            run_id              run_id for this agent (unique per parallel run)
            model_name          modelInfo.modelName
            latency_ms          Run.durationMs on the final output row
            is_final            last assistant text of the turn
            started_at          when this action began
            ended_at            when this action finished (null while in flight)

        Columns:
            id: [UUID] - PK
            conversation_id: [UUID] - FK to conversations.id
            user_message_id: [UUID] - FK to messages.id, NULL on the user prompt
            parent_id: [UUID] - FK to messages.id, action that spawned this row
            request_id: [String] - shared id for actions in one model request
            sequence: [Integer] - append order within the conversation
            kind: [String] - request or response
            role: [String] - user, assistant, tool, or system
            payload: [JSONB] - one pydantic-ai ModelMessage
            display_content: [Text] - user prompt or assistant text
            include_in_history: [Boolean] - whether this row is passed as message_history
            status: [String] - pending, complete, error, or cancelled
            run_id: [String] - this agent's run id
            user_query: [Text] - what the user asked in this turn
            agent_name: [String] - which agent performed this action
            model_name: [String] - model used for this action
            thinking: [Text] - thinking for this action
            thinking_duration_ms: [Integer] - thinking latency for this action
            tool_call_id: [String] - id linking a tool call to its result
            tool_name: [String] - tool for this action
            tool_args: [JSONB] - tool arguments
            tool_response: [JSONB] - tool result
            tool_status: [String] - running, completed, or error
            latency_ms: [Integer] - total turn latency on the final output row
            is_final: [Boolean] - whether this action is the final output
            started_at: [DateTime] - when this action started
            ended_at: [DateTime] - when this action finished
            created_at: [DateTime]
            updated_at: [DateTime]
    '''

    __tablename__ = 'messages'
    __table_args__ = (
        UniqueConstraint('conversation_id', 'sequence', name = 'uq_messages_conversation_sequence'),
        Index('ix_messages_user_message_id', 'user_message_id'),
        Index('ix_messages_parent_id', 'parent_id'),
        Index('ix_messages_request_id', 'request_id'),
        Index('ix_messages_agent_run', 'conversation_id', 'agent_name', 'run_id'),
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
    parent_id = Column(
        UUID,
        ForeignKey('messages.id', ondelete = 'CASCADE'),
        nullable = True,
    )
    request_id = Column(String, nullable = True)
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
    thinking_duration_ms = Column(Integer, nullable = True)
    tool_call_id = Column(String, nullable = True)
    tool_name = Column(String, nullable = True)
    tool_args = Column(JSONB, nullable = True)
    tool_response = Column(JSONB, nullable = True)
    tool_status = Column(String, nullable = True)
    latency_ms = Column(Integer, nullable = True)
    is_final = Column(Boolean, nullable = False, default = False)
    started_at = Column(DateTime, nullable = True)
    ended_at = Column(DateTime, nullable = True)
    created_at = Column(DateTime, nullable = False, default = datetime.now)
    updated_at = Column(DateTime, nullable = False, default = datetime.now)
