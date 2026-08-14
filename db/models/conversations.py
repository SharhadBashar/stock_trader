from datetime import datetime
import uuid
from sqlalchemy import Column, String, DateTime, UUID, ForeignKey

from db.base import Base

class Conversation(Base):
    '''
        Table to store the conversations
        Table Name: conversations
        Columns:
            id: [UUID] - PK
            user_id: [UUID] - FK to users.id
            title: [String]
            created_at: [DateTime]
            updated_at: [DateTime]
            archived_at: [DateTime]
    '''

    __tablename__ = 'conversations'

    id = Column(UUID, primary_key = True, default = uuid.uuid4)
    user_id = Column(UUID, ForeignKey('users.id'), nullable = False)
    title = Column(String, nullable = False)
    created_at = Column(DateTime, nullable = False, default = datetime.now)
    updated_at = Column(DateTime, nullable = False, default = datetime.now)
    archived_at = Column(DateTime, nullable = True)
