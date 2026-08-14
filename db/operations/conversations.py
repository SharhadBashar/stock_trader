from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from db.base_operations import BaseDBOperations
from db.models.conversations import Conversation


class ConversationsDBOperations(BaseDBOperations[Conversation]):
    def __init__(self):
        super().__init__(Conversation)

    def get_by_user_id(
        self,
        db: Session,
        user_id: UUID | None = None,
        include_archived: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Conversation]:
        query = db.query(self.model)
        if user_id is not None:
            query = query.filter(self.model.user_id == user_id)
        if not include_archived:
            query = query.filter(self.model.archived_at.is_(None))
        return (
            query.order_by(self.model.updated_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_title(self, db: Session, conversation_id: UUID, title: str) -> Conversation | None:
        return self.update(db, conversation_id, {
            'title': title,
            'updated_at': datetime.now(),
        })

    def archive(self, db: Session, conversation_id: UUID) -> Conversation | None:
        conversation = self.get(db, conversation_id)
        if not conversation:
            return None
        if conversation.archived_at is None:
            now = datetime.now()
            conversation.archived_at = now
            conversation.updated_at = now
            db.commit()
            db.refresh(conversation)
        return conversation


conversations_ops = ConversationsDBOperations()
