from datetime import datetime
import uuid

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UUID,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB

from db.base import Base


class Message(Base):
    '''
        Table to store multi-agent conversation messages
        Table Name: messages
        Each row is one event (user query, thinking, tool call, tool result, or agent output)

        Columns:
            id: [UUID] - PK
            conversation_id: [UUID] - FK to conversations.id
            user_message_id: [UUID] - FK to messages.id, NULL on the root user query
            parent_message_id: [UUID] - FK to messages.id, optional immediate parent step
            role: [String] - user, assistant, tool, or system
            msg_type: [String] - text, thinking, tool_call, tool_result, agent_output, ...
            sequence: [Integer] - append order within the user query
            sibling_index: [Integer] - concurrent sibling order, default 0
            call_id: [String] - pairs a tool call with its result
            agent_name: [String] - which agent produced this row
            parent_agent_name: [String] - agent that spawned this run
            model: [String] - model used for this row
            tool_name: [String] - tool for this action
            delegate_agent_name: [String] - agent this row delegates to
            content: [JSONB] - message body
            status: [String] - pending, running, completed, error, or cancelled
            visibility: [String] - none, agent, human, or all
            log: [JSONB] - span_id, cost_usd, latency_seconds, ...
            provider_message_id: [String] - upstream provider message id
            created_at: [DateTime]
            updated_at: [DateTime]
            archived_at: [DateTime]
    '''

    __tablename__ = 'messages'
    __table_args__ = (
        CheckConstraint(
            "(user_message_id IS NULL AND role = 'user') OR (user_message_id IS NOT NULL)",
            name = 'ck_messages_root_user',
        ),
        CheckConstraint(
            "visibility IN ('none', 'agent', 'human', 'all')",
            name = 'ck_messages_visibility',
        ),
        Index(
            'uq_messages_user_seq_sib',
            'user_message_id',
            'sequence',
            'sibling_index',
            unique = True,
            postgresql_where = text('user_message_id IS NOT NULL'),
        ),
        Index('ix_messages_conversation_id', 'conversation_id'),
        Index('ix_messages_user_message_id', 'user_message_id'),
        Index('ix_messages_parent_message_id', 'parent_message_id'),
        Index('ix_messages_call_id', 'call_id'),
        Index('ix_messages_agent_name', 'agent_name'),
        Index('ix_messages_visibility', 'visibility'),
        Index('ix_messages_conv_created', 'conversation_id', 'created_at'),
        Index(
            'ix_messages_user_order',
            'user_message_id',
            'sequence',
            'sibling_index',
            'created_at',
        ),
        Index(
            'ix_messages_archived_at',
            'archived_at',
            postgresql_where = text('archived_at IS NOT NULL'),
        ),
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
    parent_message_id = Column(
        UUID,
        ForeignKey('messages.id', ondelete = 'SET NULL'),
        nullable = True,
    )
    role = Column(String, nullable = False)
    msg_type = Column(String, nullable = False)
    sequence = Column(Integer, nullable = False)
    sibling_index = Column(Integer, nullable = False, default = 0)
    call_id = Column(String, nullable = True)
    agent_name = Column(String, nullable = True)
    parent_agent_name = Column(String, nullable = True)
    model = Column(String, nullable = True)
    tool_name = Column(String, nullable = True)
    delegate_agent_name = Column(String, nullable = True)
    content = Column(JSONB, nullable = True)
    status = Column(String, nullable = True)
    visibility = Column(String, nullable = False, default = 'all')
    log = Column(JSONB, nullable = True)
    provider_message_id = Column(String, nullable = True)
    created_at = Column(DateTime, nullable = False, default = datetime.now)
    updated_at = Column(DateTime, nullable = False, default = datetime.now)
    archived_at = Column(DateTime, nullable = True)
