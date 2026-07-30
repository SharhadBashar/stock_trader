"""
User model.

Firebase owns all credentials (passwords, OAuth, phone verification).
This table only links a Firebase account (firebase_uuid) to a local row
that the rest of the app can reference.
"""

from sqlalchemy import Column, DateTime, String, func, text
from sqlalchemy.dialects.postgresql import UUID

from db.base import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid = True), primary_key = True, server_default = text('gen_random_uuid()'))
    # Link to Firebase; lookup key on every authenticated request
    firebase_uuid = Column(String(128), nullable = False, unique = True)
    # From Firebase token claims when present
    phone = Column(String(32), nullable = True)
    email = Column(String(255), nullable = False, unique = True)
    created_at = Column(DateTime(timezone = True), nullable = False, server_default = func.now())
    updated_at = Column(DateTime(timezone = True), nullable = False, server_default = func.now(), onupdate = func.now())
    last_login = Column(DateTime(timezone = True), nullable = True)
    # Soft delete; NULL = active
    archived_at = Column(DateTime(timezone = True), nullable = True)

    def __repr__(self) -> str:
        return f'<User id={self.id} firebase_uuid={self.firebase_uuid} email={self.email}>'
