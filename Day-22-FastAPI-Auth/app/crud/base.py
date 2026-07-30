# ============================================================
# app/crud/base.py
# Generic CRUD base class for all models
# ============================================================

from typing import TypeVar, Generic, Type, Optional, Any
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Generic CRUD operations reusable for any SQLAlchemy model.

    Subclasses should call super().__init__(Model) and can
    override any method or add model-specific methods.
    """

    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get(self, db: Session, id: int) -> Optional[ModelType]:
        """Get a single record by primary key."""
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[list[ModelType], int]:
        """Get paginated records. Returns (items, total_count)."""
        query = db.query(self.model)
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    def create(self, db: Session, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record from a Pydantic schema."""
        obj_data = obj_in.model_dump()
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        db.flush()    # write to DB without committing (session.commit() happens in get_db)
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | dict
    ) -> ModelType:
        """Update an existing record."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            # exclude_unset=True → only update fields the client sent
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        db.flush()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: int) -> bool:
        """Hard delete a record. Returns False if not found."""
        obj = self.get(db, id)
        if not obj:
            return False
        db.delete(obj)
        db.flush()
        return True

    def count(self, db: Session) -> int:
        """Count total records."""
        return db.query(self.model).count()

    def exists(self, db: Session, id: int) -> bool:
        """Check if a record exists."""
        return db.query(self.model).filter(self.model.id == id).count() > 0