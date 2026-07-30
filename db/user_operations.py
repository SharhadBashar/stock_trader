"""
Database operations for the User model.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from .base_operations import BaseDBOperations
from .models import User


class UserDBOperations(BaseDBOperations[User]):
    """
    Database operations for the User model.
    Adds user specific helpers on top of the generic CRUD operations.
    """

    def __init__(self):
        super().__init__(User)

    def get_by_firebase_uuid(self, db: Session, firebase_uuid: str) -> User | None:
        """
        Get a non archived user by their Firebase uuid.

        Args:
            db: Database session
            firebase_uuid: The Firebase uid of the user

        Returns:
            The found user or None if not found
        """
        return (
            db.query(User)
            .filter(User.firebase_uuid == firebase_uuid, User.archived_at.is_(None))
            .first()
        )

    def touch_last_login(self, db: Session, user: User) -> User:
        """
        Set the user's last_login to now.

        Args:
            db: Database session
            user: The user to update

        Returns:
            The updated user
        """
        user.last_login = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)
        return user
