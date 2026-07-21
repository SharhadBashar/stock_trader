"""
Base class for database operations.
This class provides basic database operations (CRUD) that can be used with any model.
"""

from typing import Generic, TypeVar

from sqlalchemy.orm import Session

from .base import Base


# This tells Python that ModelType must be a class that inherits from Base
ModelType = TypeVar("ModelType", bound=Base)


class BaseDBOperations(Generic[ModelType]):
    """
    Base class for database operations.
    This class provides basic database operations (CRUD) that can be used with any model.

    Example usage:
    ```python
    # Create a new database operations class for your model
    class UserDBOperations(BaseDBOperations[User]):
        def __init__(self):
            super().__init__(User)

    # Use it in your code
    user_ops = UserDBOperations()
    new_user = user_ops.create(db, {'name': 'John'})
    ```
    """

    def __init__(self, model: type[ModelType]):
        """
        Initialize with the model class you want to work with.

        Args:
            model: The SQLAlchemy model class (must inherit from Base)
        """
        self.model = model

    def get(self, db: Session, record_id: str) -> ModelType | None:
        """
        Get a single record by its ID.

        Args:
            db: Database session
            record_id: The ID of the record to find

        Returns:
            The found record or None if not found
        """
        return db.query(self.model).filter(self.model.id == record_id).first()

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> list[ModelType]:
        """
        Get multiple records with pagination.

        Args:
            db: Database session
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            List of records
        """
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, data: dict) -> ModelType:
        """
        Create a new record in the database.

        Args:
            db: Database session
            data: Dictionary containing the data for the new record

        Returns:
            The newly created record
        """
        db_obj = self.model(**data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, record_id: str, data: dict) -> ModelType | None:
        """
        Update an existing record.

        Args:
            db: Database session
            record_id: ID of the record to update
            data: Dictionary containing the new data

        Returns:
            The updated record or None if not found
        """
        db_obj = self.get(db, record_id)
        if db_obj:
            for key, value in data.items():
                setattr(db_obj, key, value)
            db.commit()
            db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, record_id: str) -> bool:
        """
        Delete a record from the database.

        Args:
            db: Database session
            record_id: ID of the record to delete

        Returns:
            True if the record was deleted, False if not found
        """
        db_obj = self.get(db, record_id)
        if db_obj:
            db.delete(db_obj)
            db.commit()
            return True
        return False
