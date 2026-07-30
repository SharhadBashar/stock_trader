"""create users table

Revision ID: 68cf84b169da
Revises: 
Create Date: 2026-07-30 19:16:51.703859

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '68cf84b169da'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid = True), nullable = False),
        sa.Column('firebase_uuid', sa.Text(), nullable = False),
        sa.Column('phone', sa.Text(), nullable = True),
        sa.Column('email', sa.Text(), nullable = True),
        sa.Column('created_at', sa.DateTime(timezone = True), server_default = sa.text('now()'), nullable = False),
        sa.Column('updated_at', sa.DateTime(timezone = True), server_default = sa.text('now()'), nullable = False),
        sa.Column('last_login', sa.DateTime(timezone = True), nullable = True),
        sa.Column('archived_at', sa.DateTime(timezone = True), nullable = True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_firebase_uuid', 'users', ['firebase_uuid'], unique = True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_users_firebase_uuid', table_name = 'users')
    op.drop_table('users')
