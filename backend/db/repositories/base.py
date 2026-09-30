"""Base repository providing generic CRUD operations."""
from typing import Any, Generic, List, Optional, Type, TypeVar
from sqlalchemy.orm import Session
from backend.db.session import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic base repository for SQLAlchemy models."""

    def __init__(self, model: Type[ModelType], db: Session) -> None:
        self.model = model
        self.db = db

    def get_by_id(self, id: Any) -> Optional[ModelType]:
        """Fetch a single record by primary key."""
        return self.db.query(self.model).filter(self.model.id == id).first()

    def list_all(self, limit: int = 100, offset: int = 0) -> List[ModelType]:
        """List records with pagination."""
        return self.db.query(self.model).offset(offset).limit(limit).all()

    def count(self) -> int:
        """Return total count of records."""
        return self.db.query(self.model).count()

    def add(self, entity: ModelType) -> ModelType:
        """Add and commit an entity."""
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def add_all(self, entities: List[ModelType]) -> List[ModelType]:
        """Add and commit multiple entities."""
        self.db.add_all(entities)
        self.db.commit()
        return entities
