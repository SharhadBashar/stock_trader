from datetime import datetime
import uuid
from sqlalchemy import Column, String, DateTime, UUID

from db.base import Base

class Users(Base):
    '''
    Table to store users
    Table Name: users
    Columns:
        id: [UUID] - PK
        firebase_id: [String]
        name: [String]
        email: [String]
        created_at: [DateTime]
        updated_at: [DateTime]
        archived_at: [DateTime]
    '''

    __tablename__ = 'users'

    id = Column(UUID, primary_key = True, default = uuid.uuid4)
    firebase_id = Column(String, nullable = False, unique = True)
    name = Column(String, nullable = False)
    email = Column(String, nullable = False, unique = True)
    phone = Column(String, nullable = True)
    created_at = Column(DateTime, nullable = False, default = datetime.now)
    updated_at = Column(DateTime, nullable = False, default = datetime.now)
    archived_at = Column(DateTime, nullable = True)
