from typing import Generic, Optional, Sequence, TypeVar

from sqlmodel import SQLModel

from app.core.exceptions import EntityNotFoundError
from app.repositories.base import BaseRepository

ModelType = TypeVar("ModelType", bound=SQLModel)


class BaseService(Generic[ModelType]):
    """Shared business-rule layer sitting between routes and repositories."""

    entity_name: str = "Entity"

    def __init__(self, repository: BaseRepository):
        self.repository = repository

    def list(
        self, *, skip: int = 0, limit: int = 50, search: Optional[str] = None
    ) -> tuple[Sequence[ModelType], int]:
        return self.repository.list(skip=skip, limit=limit, search=search)

    def get(self, id_: int) -> ModelType:
        obj = self.repository.get(id_)
        if obj is None:
            raise EntityNotFoundError(self.entity_name, id_)
        return obj

    def create(self, data: dict) -> ModelType:
        self.validate_references(data)
        self.validate_duplicate(data)
        obj = self.repository.model(**data)
        return self.repository.create(obj)

    def update(self, id_: int, data: dict) -> ModelType:
        obj = self.get(id_)
        clean = {k: v for k, v in data.items() if v is not None}
        self.validate_references(clean)
        self.validate_duplicate(clean, exclude_id=id_)
        return self.repository.update(obj, clean)

    def delete(self, id_: int) -> None:
        obj = self.get(id_)
        self.repository.delete(obj)

    def validate_duplicate(self, data: dict, exclude_id: Optional[int] = None) -> None:
        """Override to enforce natural-key uniqueness beyond DB constraints."""

    def validate_references(self, data: dict) -> None:
        """Override to verify foreign keys point at existing rows."""
