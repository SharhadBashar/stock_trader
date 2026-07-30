"""create users table

Revision ID: bc8479ea971d
Revises:
Create Date: 2026-07-30 19:10:52.216073

Hand-written initial migration (no live DB was available for autogenerate).
Requires Postgres 13+ where gen_random_uuid() is built in; on older versions
enable pgcrypto first (CREATE EXTENSION pgcrypto).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'bc8479ea971d'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the users table."""
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid = True), server_default = sa.text('gen_random_uuid()'), nullable = False),
        sa.Column('firebase_uuid', sa.String(length = 128), nullable = False),
        sa.Column('phone', sa.String(length = 32), nullable = True),
        sa.Column('email', sa.String(length = 255), nullable = False),
        sa.Column('created_at', sa.DateTime(timezone = True), server_default = sa.text('now()'), nullable = False),
        sa.Column('updated_at', sa.DateTime(timezone = True), server_default = sa.text('now()'), nullable = False),
        sa.Column('last_login', sa.DateTime(timezone = True), nullable = True),
        sa.Column('archived_at', sa.DateTime(timezone = True), nullable = True),
        sa.PrimaryKeyConstraint('id', name = 'pk_users'),
        sa.UniqueConstraint('firebase_uuid', name = 'uq_users_firebase_uuid'),
        sa.UniqueConstraint('email', name = 'uq_users_email'),
    )


def downgrade() -> None:
    """Drop the users table."""
    op.drop_table('users')
