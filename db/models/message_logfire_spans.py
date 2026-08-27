from datetime import datetime
import uuid

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    UUID,
)

from db.base import Base


class MessageLogfireSpan(Base):
    '''
        Table to map a conversation message to its Logfire / OpenTelemetry span.

        Table Name: message_logfire_spans
        One message can have many spans (for example a tool row plus its
        nested chat span). A (trace_id, span_id) pair maps to one row.
        conversation_id is denormalized so spans can be queried per conversation
        without joining messages.

        Columns:
            id: [UUID] - PK
            conversation_id: [UUID] - FK to conversations.id
            message_id: [UUID] - FK to messages.id
            trace_id: [String] - Logfire / OTel trace id
            span_id: [String] - Logfire / OTel span id
            created_at: [DateTime]
    '''

    __tablename__ = 'message_logfire_spans'
    __table_args__ = (
        UniqueConstraint(
            'message_id',
            'span_id',
            name = 'uq_message_logfire_spans_message_span',
        ),
        UniqueConstraint(
            'trace_id',
            'span_id',
            name = 'uq_message_logfire_spans_trace_span',
        ),
        Index('ix_message_logfire_spans_conversation_id', 'conversation_id'),
        Index('ix_message_logfire_spans_message_id', 'message_id'),
        Index('ix_message_logfire_spans_span_id', 'span_id'),
        Index('ix_message_logfire_spans_trace_id', 'trace_id'),
    )

    id = Column(UUID, primary_key = True, default = uuid.uuid4)
    conversation_id = Column(
        UUID,
        ForeignKey('conversations.id', ondelete = 'CASCADE'),
        nullable = False,
    )
    message_id = Column(
        UUID,
        ForeignKey('messages.id', ondelete = 'CASCADE'),
        nullable = True,
    )
    trace_id = Column(String, nullable = False)
    span_id = Column(String, nullable = False)
    created_at = Column(DateTime, nullable = False, default = datetime.now)
