"""
SQLAlchemy models.

Importing this package registers every model on Base.metadata,
which is what alembic uses for autogenerate support.
"""

from db.models.user import User


__all__ = ['User']
