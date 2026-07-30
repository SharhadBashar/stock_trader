"""
Database models.
Tables are defined using the SQLAlchemy 2.0 Mapped / mapped_column style.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class User(Base):
    __tablename__ = 'users'
    __table_args__ = (
        Index('ix_users_firebase_uuid', 'firebase_uuid', unique = True),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid = True), primary_key = True, default = uuid.uuid4
    )
    firebase_uuid: Mapped[str] = mapped_column(Text, nullable = False)
    phone: Mapped[str | None] = mapped_column(Text, nullable = True)
    email: Mapped[str | None] = mapped_column(Text, nullable = True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone = True), server_default = func.now(), nullable = False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        server_default = func.now(),
        onupdate = func.now(),
        nullable = False,
    )
    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone = True), nullable = True
    )
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone = True), nullable = True
    )
