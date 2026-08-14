from sqlalchemy.orm import Session

from db.base_operations import BaseDBOperations
from db.models.users import Users


class UsersDBOperations(BaseDBOperations[Users]):
    def __init__(self):
        super().__init__(Users)

    def get_by_firebase_id(self, db: Session, firebase_id: str) -> Users | None:
        return db.query(self.model).filter(self.model.firebase_id == firebase_id).first()

    def get_by_email(self, db: Session, email: str) -> Users | None:
        return db.query(self.model).filter(self.model.email == email).first()


users_ops = UsersDBOperations()
