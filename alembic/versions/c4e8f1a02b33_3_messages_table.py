"""3:messages_table

Revision ID: c4e8f1a02b33
Revises: fdeae32eaf44
Create Date: 2026-09-17 20:52:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c4e8f1a02b33'
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
        sa.Column('parent_message_id', sa.UUID(), nullable = True),
        sa.Column('role', sa.String(), nullable = False),
        sa.Column('msg_type', sa.String(), nullable = False),
        sa.Column('sequence', sa.Integer(), nullable = False),
        sa.Column('sibling_index', sa.Integer(), nullable = False, server_default = '0'),
        sa.Column('call_id', sa.String(), nullable = True),
        sa.Column('agent_name', sa.String(), nullable = True),
        sa.Column('parent_agent_name', sa.String(), nullable = True),
        sa.Column('model', sa.String(), nullable = True),
        sa.Column('tool_name', sa.String(), nullable = True),
        sa.Column('delegate_agent_name', sa.String(), nullable = True),
        sa.Column('content', postgresql.JSONB(astext_type = sa.Text()), nullable = True),
        sa.Column('status', sa.String(), nullable = True),
        sa.Column('visibility', sa.String(), nullable = False, server_default = 'all'),
        sa.Column('log', postgresql.JSONB(astext_type = sa.Text()), nullable = True),
        sa.Column('provider_message_id', sa.String(), nullable = True),
        sa.Column('created_at', sa.DateTime(), nullable = False),
        sa.Column('updated_at', sa.DateTime(), nullable = False),
        sa.Column('archived_at', sa.DateTime(), nullable = True),
        sa.CheckConstraint(
            "(user_message_id IS NULL AND role = 'user') OR (user_message_id IS NOT NULL)",
            name = 'ck_messages_root_user',
        ),
        sa.CheckConstraint(
            "visibility IN ('none', 'agent', 'human', 'all')",
            name = 'ck_messages_visibility',
        ),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete = 'CASCADE'),
        sa.ForeignKeyConstraint(['user_message_id'], ['messages.id'], ondelete = 'CASCADE'),
        sa.ForeignKeyConstraint(['parent_message_id'], ['messages.id'], ondelete = 'SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'uq_messages_user_seq_sib',
        'messages',
        ['user_message_id', 'sequence', 'sibling_index'],
        unique = True,
        postgresql_where = sa.text('user_message_id IS NOT NULL'),
    )
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'], unique = False)
    op.create_index('ix_messages_user_message_id', 'messages', ['user_message_id'], unique = False)
    op.create_index('ix_messages_parent_message_id', 'messages', ['parent_message_id'], unique = False)
    op.create_index('ix_messages_call_id', 'messages', ['call_id'], unique = False)
    op.create_index('ix_messages_agent_name', 'messages', ['agent_name'], unique = False)
    op.create_index('ix_messages_visibility', 'messages', ['visibility'], unique = False)
    op.create_index('ix_messages_conv_created', 'messages', ['conversation_id', 'created_at'], unique = False)
    op.create_index(
        'ix_messages_user_order',
        'messages',
        ['user_message_id', 'sequence', 'sibling_index', 'created_at'],
        unique = False,
    )
    op.create_index(
        'ix_messages_archived_at',
        'messages',
        ['archived_at'],
        unique = False,
        postgresql_where = sa.text('archived_at IS NOT NULL'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_messages_archived_at', table_name = 'messages')
    op.drop_index('ix_messages_user_order', table_name = 'messages')
    op.drop_index('ix_messages_conv_created', table_name = 'messages')
    op.drop_index('ix_messages_visibility', table_name = 'messages')
    op.drop_index('ix_messages_agent_name', table_name = 'messages')
    op.drop_index('ix_messages_call_id', table_name = 'messages')
    op.drop_index('ix_messages_parent_message_id', table_name = 'messages')
    op.drop_index('ix_messages_user_message_id', table_name = 'messages')
    op.drop_index('ix_messages_conversation_id', table_name = 'messages')
    op.drop_index('uq_messages_user_seq_sib', table_name = 'messages')
    op.drop_table('messages')
