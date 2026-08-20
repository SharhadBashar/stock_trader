"""3:messages_table

Revision ID: c3a91f7b4d20
Revises: fdeae32eaf44
Create Date: 2026-08-20 04:24:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c3a91f7b4d20'
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


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_messages_history', table_name = 'messages')
    op.drop_index('ix_messages_user_message_id', table_name = 'messages')
    op.drop_table('messages')
