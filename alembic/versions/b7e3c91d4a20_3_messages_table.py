"""3:messages_table

Revision ID: b7e3c91d4a20
Revises: fdeae32eaf44
Create Date: 2026-08-26 05:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b7e3c91d4a20'
down_revision: Union[str, Sequence[str], None] = 'fdeae32eaf44'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'messages',
        sa.Column('id', sa.UUID(), nullable = False),
        sa.Column('conversation_id', sa.UUID(), nullable = False),
        sa.Column('user_message_id', sa.UUID(), nullable = True),
        sa.Column('sequence', sa.Integer(), nullable = False),
        sa.Column('kind', sa.String(), nullable = False),
        sa.Column('role', sa.String(), nullable = False),
        sa.Column('payload', postgresql.JSONB(astext_type = sa.Text()), nullable = False),
        sa.Column('display_content', sa.Text(), nullable = True),
        sa.Column('include_in_history', sa.Boolean(), nullable = False),
        sa.Column('status', sa.String(), nullable = False),
        sa.Column('run_id', sa.String(), nullable = True),
        sa.Column('user_query', sa.Text(), nullable = True),
        sa.Column('agents_called', postgresql.JSONB(astext_type = sa.Text()), nullable = True),
        sa.Column('agent_steps', postgresql.JSONB(astext_type = sa.Text()), nullable = True),
        sa.Column('tools_called', postgresql.JSONB(astext_type = sa.Text()), nullable = True),
        sa.Column('tool_responses', postgresql.JSONB(astext_type = sa.Text()), nullable = True),
        sa.Column('thinking', sa.Text(), nullable = True),
        sa.Column('agent_name', sa.String(), nullable = True),
        sa.Column('model_name', sa.String(), nullable = True),
        sa.Column('latency_ms', sa.Integer(), nullable = True),
        sa.Column('is_final', sa.Boolean(), nullable = False),
        sa.Column('created_at', sa.DateTime(), nullable = False),
        sa.Column('updated_at', sa.DateTime(), nullable = False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete = 'CASCADE'),
        sa.ForeignKeyConstraint(['user_message_id'], ['messages.id'], ondelete = 'CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('conversation_id', 'sequence', name = 'uq_messages_conversation_sequence'),
    )
    op.create_index('ix_messages_user_message_id', 'messages', ['user_message_id'], unique = False)
    op.create_index(
        'ix_messages_history',
        'messages',
        ['conversation_id', 'sequence'],
        unique = False,
        postgresql_where = sa.text('include_in_history IS TRUE'),
    )
    op.create_index(
        'ix_messages_is_final',
        'messages',
        ['conversation_id', 'is_final'],
        unique = False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_messages_is_final', table_name = 'messages')
    op.drop_index('ix_messages_history', table_name = 'messages')
    op.drop_index('ix_messages_user_message_id', table_name = 'messages')
    op.drop_table('messages')
